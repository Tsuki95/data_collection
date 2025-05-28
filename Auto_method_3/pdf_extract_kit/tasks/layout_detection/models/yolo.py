import os
import cv2
import torch
import numpy as np
import json
from PIL import ImageEnhance
import docx
from docx.shared import Inches
from paddleocr import PaddleOCR
from pdf_extract_kit.registry import MODEL_REGISTRY
from pdf_extract_kit.utils.visualization import visualize_bbox
from pdf_extract_kit.dataset.dataset import ImageDataset

####added when some packages are not compatible
####import os
####os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

@MODEL_REGISTRY.register('layout_detection_yolo')
class LayoutDetectionYOLO:
    def __init__(self, config, word_path):
        """
        Initialize the LayoutDetectionYOLO class.

        Args:
            config (dict): Configuration dictionary containing model parameters.
            word_path (str): Path to the word document.
        """
        self.config = config
        self.word_path= word_path

        # Mapping from class IDs to class names
        self.id_to_names = {
            0: 'title', 
            1: 'plain text',
            2: 'abandon', 
            3: 'figure', 
            4: 'figure_caption', 
            5: 'table', 
            6: 'table_caption', 
            7: 'table_footnote', 
            8: 'isolate_formula', 
            9: 'formula_caption'
        }

        # Load the YOLO model from the specified path
        try:
            from doclayout_yolo import YOLOv10
            self.model = YOLOv10(config['model_path'])
        except AttributeError:
            from ultralytics import YOLO
            self.model = YOLO(config['model_path'])

        # Set model parameters
        self.img_size = config.get('img_size', 1280)
        self.conf_thres = config.get('conf_thres', 0.25)
        self.iou_thres = config.get('iou_thres', 0.45)
        self.visualize = config.get('visualize', False)
        self.nc = config.get('nc', 10)
        self.workers = config.get('workers', 8)
        self.device = config.get('device', 'cpu')
        
        if self.iou_thres > 0:
            import torchvision
            self.nms_func = torchvision.ops.nms

        self.ocr = PaddleOCR(use_angle_cls=True, lang="en")  


    def extract_text(self, image, bbox):
        """
        Extract text content from a given bounding box.
        """
        margin = 20  
        cropped_image = image.crop((
            max(0, bbox[0] - margin),
            max(0, bbox[1] - margin),
            min(image.width, bbox[2] + margin),
            min(image.height, bbox[3] + margin)
        ))
        enhancer = ImageEnhance.Contrast(cropped_image)
        cropped_image = enhancer.enhance(2.0)  
        cropped_image_np = np.array(cropped_image)[:, :, ::-1]  
        ocr_result = self.ocr.ocr(cropped_image_np)  
        if not ocr_result or not ocr_result[0]:
            return ""
        text_content = "\n".join([line[1][0] for line in ocr_result[0]])
        return text_content

    def save_to_word(self, extracted_items):
        """
        Save extracted tables and figures along with their captions to a Word document.

        Args:
            extracted_items (list): List of tuples containing image paths and captions.
        """
        doc = docx.Document(self.word_path)

        doc.add_heading("相关结构图片：", level=2)  

        for item in extracted_items:
            if 'image_path' in item:
                doc.add_picture(item['image_path'], width=Inches(4))
            if 'caption' in item:
                doc.add_paragraph(item['caption'])

        try:
            doc.save(self.word_path)
        except Exception as e:
            print(f"Error saving Word file: {e}")
            raise
        print(f"Word document updated and saved at {self.word_path}")

    def load_image_codes_from_docx(self):
        """
        Load all image codes (e.g., "Scheme 数字", "Table 数字", "Figure 数字") from a single-paragraph Word document.

        Returns:
            list: List of unique image codes, excluding unwanted fields like '未提供'.
        """
        image_codes = []
        doc = docx.Document(self.word_path)
        
        for paragraph in doc.paragraphs:
            lines = paragraph.text.split("\n")
            for line in lines:
                if "9. 图片代号：" in line:
                    code_text = line.split("9. 图片代号：")[-1].strip()
                    codes = [code.strip() for code in code_text.split(",") if code.strip()]
                    image_codes.extend(codes)  

        image_codes = list(set(code for code in image_codes if code != '未提供'))
        return image_codes


    def predict(self, images, result_path, image_ids=None):
        if not os.path.exists(result_path):
            os.makedirs(result_path)

        # Load valid image codes from Word document
        valid_image_codes = self.load_image_codes_from_docx()

        extracted_items = []  

        for idx, image in enumerate(images):
            result = self.model.predict(image, imgsz=self.img_size, conf=self.conf_thres, iou=self.iou_thres, verbose=False, device=self.device)[0]

            if self.visualize:
                boxes = result.__dict__['boxes'].xyxy  
                classes = result.__dict__['boxes'].cls  
                scores = result.__dict__['boxes'].conf  

                if self.iou_thres > 0:
                    indices = self.nms_func(
                        boxes=torch.Tensor(boxes),
                        scores=torch.Tensor(scores),
                        iou_threshold=self.iou_thres
                    )
                    boxes, scores, classes = boxes[indices], scores[indices], classes[indices]

                for i, (box, cls, score) in enumerate(zip(boxes, classes, scores)):
                    category_type = self.id_to_names[int(cls)]
                    identifier = f"page_{idx + 1}_{category_type}_{i + 1}"  

                    if category_type in ["figure_caption", "table_caption"]:
                        caption_bbox = [int(coord) for coord in box.tolist()]  
                        caption_text = self.extract_text(image, caption_bbox)  
                        print(f"Page {idx + 1}: Detected {category_type} at {caption_bbox} with identifier {identifier}")

                        if any(code in caption_text for code in valid_image_codes):
                            min_distance = float("inf")  
                            matched_bbox = None  

                            for k, (box, cls) in enumerate(zip(boxes, classes)):
                                if self.id_to_names[int(cls)] in ["figure", "table"]:
                                    bbox = [int(coord) for coord in box.tolist()]  

                                    distance1 = min(
                                        abs(caption_bbox[1] - bbox[3]),  
                                        abs(caption_bbox[3] - bbox[1])   
                                    )
                                    distance2 = max(
                                        abs(caption_bbox[0] - bbox[0]),  
                                        abs(caption_bbox[2] - bbox[2])   
                                    )

                                    if distance2 < 400 and distance1 < min_distance:
                                        min_distance = distance1
                                        matched_bbox = bbox

                            if matched_bbox:
                                save_path = os.path.join(result_path, f"{identifier}.png")
                                cropped_image = image.crop((matched_bbox[0], matched_bbox[1], matched_bbox[2], matched_bbox[3]))
                                cropped_image.save(save_path)  

                                extracted_items.append({
                                    "image_path": save_path,
                                    "caption": caption_text
                                })  

        self.save_to_word(extracted_items)
        print(f"Layout analysis completed. Results saved in {result_path}")
