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

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

@MODEL_REGISTRY.register('layout_detection_yolo')
class LayoutDetectionYOLO:
    def __init__(self, config):
        """
        Initialize the LayoutDetectionYOLO class.

        Args:
            config (dict): Configuration dictionary containing model parameters.
        """
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

        # 初始化 PaddleOCR
        self.ocr = PaddleOCR(use_angle_cls=True, lang="en")  # 支持多语言，可以根据需要更改 lang 参数


    def extract_text(self, image, bbox):
        """
        Extract text content from a given bounding box.
        """
        margin = 20  # 设置边距
        cropped_image = image.crop((
            max(0, bbox[0] - margin),
            max(0, bbox[1] - margin),
            min(image.width, bbox[2] + margin),
            min(image.height, bbox[3] + margin)
        ))
        enhancer = ImageEnhance.Contrast(cropped_image)
        cropped_image = enhancer.enhance(2.0)  # 增强对比度
        cropped_image_np = np.array(cropped_image)[:, :, ::-1]  # Convert to BGR format for PaddleOCR
        ocr_result = self.ocr.ocr(cropped_image_np)  # 调用 OCR
        if not ocr_result or not ocr_result[0]:
            # 如果 OCR 结果为空，返回空字符串
            return ""
        # 拼接识别的文本行
        text_content = "\n".join([line[1][0] for line in ocr_result[0]])
        return text_content


    """
    这是原本的代码块
    def predict(self, images, result_path, image_ids=None):
    
        Predict formulas in images.

        Args:
            images (list): List of images to be predicted.
            result_path (str): Path to save the prediction results.
            image_ids (list, optional): List of image IDs corresponding to the images.

        Returns:
            list: List of prediction results.

        results = []
        for idx, image in enumerate(images):
            result = self.model.predict(image, imgsz=self.img_size, conf=self.conf_thres, iou=self.iou_thres, verbose=False, device=self.device)[0]
            if self.visualize:
                if not os.path.exists(result_path):
                    os.makedirs(result_path)
                boxes = result.__dict__['boxes'].xyxy
                classes = result.__dict__['boxes'].cls
                scores = result.__dict__['boxes'].conf

                if self.iou_thres > 0:
                    indices = self.nms_func(boxes=torch.Tensor(boxes), scores=torch.Tensor(scores),iou_threshold=self.iou_thres)
                    boxes, scores, classes = boxes[indices], scores[indices], classes[indices]
                    if len(boxes.shape) == 1:
                        boxes = np.expand_dims(boxes, 0)
                        scores = np.expand_dims(scores, 0)
                        classes = np.expand_dims(classes, 0)
                
                vis_result = visualize_bbox(image, boxes, classes, scores, self.id_to_names)

                # Determine the base name of the image
                if image_ids:
                    base_name = image_ids[idx]
                else:
                    # base_name = os.path.basename(image)
                    base_name = os.path.splitext(os.path.basename(image))[0]  # Remove file extension
                
                result_name = f"{base_name}_layout.png"
                
                # Save the visualized result                
                cv2.imwrite(os.path.join(result_path, result_name), vis_result)
            results.append(result)
        return results
    """
    
    """
    这是生成json文件的代码块
    def predict(self, images, result_path, image_ids=None):
        if not os.path.exists(result_path):
            os.makedirs(result_path)

        json_results = []  # 保存所有页面的布局结果
        for idx, image in enumerate(images):
            # 运行模型预测
            result = self.model.predict(image, imgsz=self.img_size, conf=self.conf_thres, iou=self.iou_thres, verbose=False, device=self.device)[0]
            
            page_results = []  # 保存当前页面的布局结果
            if self.visualize:
                boxes = result.__dict__['boxes'].xyxy  # 提取边界框
                classes = result.__dict__['boxes'].cls  # 提取类别
                scores = result.__dict__['boxes'].conf  # 提取置信度

                if self.iou_thres > 0:
                    indices = self.nms_func(
                        boxes=torch.Tensor(boxes),
                        scores=torch.Tensor(scores),
                        iou_threshold=self.iou_thres
                    )
                    boxes, scores, classes = boxes[indices], scores[indices], classes[indices]

                for i, (box, cls, score) in enumerate(zip(boxes, classes, scores)):
                    category_type = self.id_to_names[int(cls)]
                    bbox = [int(coord) for coord in box.tolist()]  # 边界框坐标
                    identifier = f"page_{idx + 1}_{category_type}_{i + 1}"  # 唯一标识符

                    print(f"Page {idx + 1}: Detected {category_type} at {bbox} with identifier {identifier}")

                    if category_type in ["figure", "table"]:
                        save_path = os.path.join(result_path, f"{identifier}.png")
                        cropped_image = image.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
                        cropped_image.save(save_path)
                        result_entry = {
                            "identifier": identifier,
                            "category": category_type,
                            "bbox": bbox,
                            "content": f"Image saved at: {save_path}"
                        }
                    else:
                        text_content = self.extract_text(image, bbox)
                        result_entry = {
                            "identifier": identifier,
                            "category": category_type,
                            "bbox": bbox,
                            "content": text_content
                        }
                    
                    page_results.append(result_entry)

            json_results.append({
                "page": idx + 1,
                "detections": page_results
            })

        json_output_path = os.path.join(result_path, "layout_analysis.json")
        with open(json_output_path, "w", encoding="utf-8") as json_file:
            json.dump(json_results, json_file, indent=4)

        print(f"Layout analysis completed. Results saved in {result_path}")
        return json_results
        """
    def save_to_word(self, docx_path, extracted_items):
        """
        Append extracted tables and figures along with their captions to an existing Word document.

        Args:
            docx_path (str): Path to the existing Word document.
            extracted_items (list): List of dictionaries containing image paths and captions.
        """
        # 打开现有的 Word 文档
        doc = docx.Document(docx_path)

        # 在文档末尾添加标题
        doc.add_heading("相关结构图片：", level=2)  # 添加二级标题

        # 遍历提取的项目并添加到文档中
        for item in extracted_items:
            if 'image_path' in item:
                # 添加图片
                doc.add_picture(item['image_path'], width=Inches(4))
            if 'caption' in item:
                # 添加图片对应的标题或说明文字
                doc.add_paragraph(item['caption'])

        # 保存修改后的文档
        doc.save(docx_path)
        print(f"Word document updated and saved at {docx_path}")

    def load_image_codes_from_docx(self, docx_path):
        """
        Load all image codes (e.g., "Scheme 数字", "Table 数字", "Figure 数字") from a single-paragraph Word document.

        Args:
            docx_path (str): Path to the Word document.

        Returns:
            list: List of unique image codes, excluding unwanted fields like '未提供'.
        """
        image_codes = []
        doc = docx.Document(docx_path)
        
        # 假设整个文档只有一个段落
        for paragraph in doc.paragraphs:
            # 将段落内容按换行符分割为多行
            lines = paragraph.text.split("\n")
            for line in lines:
                if "9. 图片代号：" in line:
                    # 提取 "9. 图片代号：" 后的内容
                    code_text = line.split("9. 图片代号：")[-1].strip()
                    # 将内容按逗号分隔，并逐个加入列表
                    codes = [code.strip() for code in code_text.split(",") if code.strip()]
                    image_codes.extend(codes)  # 将提取的代码加入主列表

        # 去重并过滤掉 '未提供'
        image_codes = list(set(code for code in image_codes if code != '未提供'))
        return image_codes


    def predict(self, images, result_path, image_ids=None):
        if not os.path.exists(result_path):
            os.makedirs(result_path)

        # Load valid image codes from Word document
        valid_image_codes = self.load_image_codes_from_docx(r"E:\crawler\redox_analysis_filtered.docx")

        extracted_items = []  # 用于保存提取的表格和图片及其标题

        for idx, image in enumerate(images):
            # 运行模型预测
            result = self.model.predict(image, imgsz=self.img_size, conf=self.conf_thres, iou=self.iou_thres, verbose=False, device=self.device)[0]

            if self.visualize:
                boxes = result.__dict__['boxes'].xyxy  # 提取边界框
                classes = result.__dict__['boxes'].cls  # 提取类别
                scores = result.__dict__['boxes'].conf  # 提取置信度

                if self.iou_thres > 0:
                    indices = self.nms_func(
                        boxes=torch.Tensor(boxes),
                        scores=torch.Tensor(scores),
                        iou_threshold=self.iou_thres
                    )
                    boxes, scores, classes = boxes[indices], scores[indices], classes[indices]

                for i, (box, cls, score) in enumerate(zip(boxes, classes, scores)):
                    category_type = self.id_to_names[int(cls)]
                    identifier = f"page_{idx + 1}_{category_type}_{i + 1}"  # 唯一标识符

                    #matched_items = set()  # 用于记录已经匹配的figure和table，避免重复

                    # 遍历所有的boxes和classes，找到所有figure_caption和table_caption
                    if category_type in ["figure_caption", "table_caption"]:
                        caption_bbox = [int(coord) for coord in box.tolist()]  # 边界框坐标
                        caption_text = self.extract_text(image, caption_bbox)  # 提取caption文本内容
                        print(f"Page {idx + 1}: Detected {category_type} at {caption_bbox} with identifier {identifier}")

                        # 检查caption是否包含在valid_image_codes中
                        if any(code in caption_text for code in valid_image_codes):
                            min_distance = float("inf")  # 初始化较大的最小距离
                            matched_bbox = None  # 用于保存与caption匹配的figure或table的bbox

                            # 遍历所有的boxes和classes，找到对应的figure或table
                            for k, (box, cls) in enumerate(zip(boxes, classes)):
                                if self.id_to_names[int(cls)] in ["figure", "table"]:
                                    bbox = [int(coord) for coord in box.tolist()]  # 获取figure或table的边界框

                                    # 计算当前caption与figure或table的距离
                                    distance1 = min(
                                        abs(caption_bbox[1] - bbox[3]),  # caption顶部到图片底部的距离
                                        abs(caption_bbox[3] - bbox[1])   # caption底部到图片顶部的距离
                                    )
                                    distance2 = max(
                                        abs(caption_bbox[0] - bbox[0]),  # caption左侧到图片右侧的距离
                                        abs(caption_bbox[2] - bbox[2])   # caption右侧到图片左侧的距离
                                    )

                                    # 如果符合距离条件，更新最小距离和匹配的bbox
                                    #if distance2 < 400 and distance1 < min_distance and (k not in matched_items):
                                    if distance2 < 400 and distance1 < min_distance:
                                        min_distance = distance1
                                        matched_bbox = bbox
                                        #matched_items.add(k)  # 标记这个figure或table已经匹配过

                            # 如果找到匹配的figure或table，则保存图片和caption
                            if matched_bbox:
                                save_path = os.path.join(result_path, f"{identifier}.png")
                                cropped_image = image.crop((matched_bbox[0], matched_bbox[1], matched_bbox[2], matched_bbox[3]))
                                cropped_image.save(save_path)  # 保存图片

                                extracted_items.append({
                                    "image_path": save_path,
                                    "caption": caption_text
                                })  # 保存图片路径和caption文本
        # 保存到Word文档
        self.save_to_word(r"E:\crawler\redox_analysis_filtered.docx", extracted_items)
        print(f"Layout analysis completed. Results saved in {result_path}")

"""
    将提取的所有表格和图片及其标题保存到Word文档
    def predict(self, images, result_path, image_ids=None):
        if not os.path.exists(result_path):
            os.makedirs(result_path)

        extracted_items = []  # 用于保存提取的表格和图片及其标题

        for idx, image in enumerate(images):
            # 运行模型预测
            result = self.model.predict(image, imgsz=self.img_size, conf=self.conf_thres, iou=self.iou_thres, verbose=False, device=self.device)[0]

            if self.visualize:
                boxes = result.__dict__['boxes'].xyxy  # 提取边界框
                classes = result.__dict__['boxes'].cls  # 提取类别
                scores = result.__dict__['boxes'].conf  # 提取置信度

                if self.iou_thres > 0:
                    indices = self.nms_func(
                        boxes=torch.Tensor(boxes),
                        scores=torch.Tensor(scores),
                        iou_threshold=self.iou_thres
                    )
                    boxes, scores, classes = boxes[indices], scores[indices], classes[indices]

                for i, (box, cls, score) in enumerate(zip(boxes, classes, scores)):
                    category_type = self.id_to_names[int(cls)]
                    bbox = [int(coord) for coord in box.tolist()]  # 边界框坐标
                    identifier = f"page_{idx + 1}_{category_type}_{i + 1}"  # 唯一标识符

                    print(f"Page {idx + 1}: Detected {category_type} at {bbox} with identifier {identifier}")

                    if category_type in ["figure", "table"]:
                        # 保存图片
                        save_path = os.path.join(result_path, f"{identifier}.png")
                        cropped_image = image.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
                        cropped_image.save(save_path)

                        # 提取对应的caption
                        caption = ""  # 初始化一个空字符串，用于存储提取的caption
                        min_distance = float("inf")  # 初始化一个较大的最小距离，用于比较

                        for j, (box_caption, cls_caption) in enumerate(zip(boxes, classes)):  # 遍历boxes和classes的每个元素
                            if self.id_to_names[int(cls_caption)] == f"{category_type}_caption":  # 检查当前类别是否与目标类别匹配
                                caption_bbox = [int(coord) for coord in box_caption.tolist()]  # 将box_caption转换为整数列表，表示caption的边界框坐标
                                
                                # 计算当前caption区域与cropped_image的上下距离
                                distance1 = min(
                                    abs(caption_bbox[1] - bbox[3]),  # caption顶部到图片底部的距离
                                    abs(caption_bbox[3] - bbox[1])   # caption底部到图片顶部的距离
                                )

                                distance2 = max(
                                    abs(caption_bbox[0] - bbox[0]),  # caption左侧到图片右侧的距离
                                    abs(caption_bbox[2] - bbox[2])   # caption右侧到图片左侧的距离
                                )
                                
                                if distance2 < 400:
                                    # 如果当前caption区域比之前的更接近，更新最小距离和caption
                                    if distance1 < min_distance:
                                        min_distance = distance1
                                        caption = self.extract_text(image, caption_bbox)  # 提取caption文本内容

                        extracted_items.append({
                            "image_path": save_path,
                            "caption": caption
                        })
        # 保存到Word文档
        self.save_to_word(result_path, extracted_items)
        print(f"Layout analysis completed. Results saved in {result_path}")
"""