# -*- coding: utf-8 -*-
# Suqi 20250117
import os
import sys
import argparse
mineru_path = r'E:\\crawler\\MinerU\\MinerU-master\\magic_pdf'  # 替换为你的 MinerU 路径
sys.path.append(mineru_path)

from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
import os

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Process PDF to Markdown")
parser.add_argument("--pdf_path", required=True, help="Path to the PDF file")
parser.add_argument("--image_dir", required=True, help="Directory to save images")
parser.add_argument("--markdown_dir", required=True, help="Directory to save markdown")
args = parser.parse_args()

# Get path parameters
pdf_file_name = args.pdf_path
local_image_dir = args.image_dir
local_md_dir = args.markdown_dir

# Process file name and target path
file_name = os.path.basename(pdf_file_name).split(".")[0]  # Extract file name
name_without_suff = os.path.join(local_md_dir, file_name)  # Generate target path

print(f"PDF file name: {pdf_file_name}")
print(f"Image directory: {local_image_dir}")
print(f"Markdown directory: {local_md_dir}")
print(f"Target markdown path: {name_without_suff}")

# Ensure the directories exist
os.makedirs(local_image_dir, exist_ok=True)
os.makedirs(local_md_dir, exist_ok=True)

image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
image_dir = str(os.path.basename(local_image_dir))

# Read the PDF file
reader1 = FileBasedDataReader("")
pdf_bytes = reader1.read(pdf_file_name)  # Read the PDF content

# Process the PDF file
ds = PymuDocDataset(pdf_bytes)
print("Dataset created successfully.")

if ds.classify() == SupportedPdfParseMethod.OCR:
    print("PDF classified as OCR mode.")
    infer_result = ds.apply(doc_analyze, ocr=True)
    print("Inference result generated for OCR mode.")
    pipe_result = infer_result.pipe_ocr_mode(image_writer)
    print("Pipeline result generated for OCR mode.")
else:
    print("PDF classified as text mode.")
    infer_result = ds.apply(doc_analyze, ocr=False)
    print("Inference result generated for text mode.")
    pipe_result = infer_result.pipe_txt_mode(image_writer)
    print("Pipeline result generated for text mode.")

# Export Markdown
print("Dumping markdown...")
pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
print("Markdown file dumped.")