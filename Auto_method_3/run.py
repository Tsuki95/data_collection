# -*- coding: utf-8 -*-
# Suqi 20250117
import subprocess
import sys
import os
import shutil

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

print("Current working directory:", os.getcwd())

BASE_DIR = os.path.abspath(".")
WORD_FILE_PATH = os.path.abspath("redox_analysis_filtered.docx")  # 保存提取后的文本的文件路径
PDF_DIR_PATH = r'E:\\crawler\\PDF-Extract-Kit-main\\assets\\demo\\layout_detection'  # PDF 文件所在的文件夹路径
OUTPUT_DIR_PATH = r'E:\\crawler\\PDF-Extract-Kit-main\\outputs\\layout_detection'  # 输出文件夹路径

# Define the path to askgpt.py
ASKGPT_SCRIPT_PATH = os.path.join(BASE_DIR, "askgpt.py")

def run_askgpt(word_file_path, pdf_file_path):
    try:
        print(f"Running askgpt.py for {pdf_file_path}...")
        subprocess.run(
            ["python", ASKGPT_SCRIPT_PATH, "--word_file", word_file_path, "--pdf_file", pdf_file_path],
            check=True
        )
        print(f"askgpt.py finished successfully for {pdf_file_path}.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running askgpt.py for {pdf_file_path}: {e}")
        sys.exit(1)

def run_layout_detection(word_file_path, pdf_file_path):
    """
    Run the layout_detection.py script and pass the Word file path as an argument.
    """
    try:
        print(f"Running layout_detection.py for {pdf_file_path}...")
        subprocess.run(["python", "scripts/layout_detection.py", "--config=configs/layout_detection_yolo.yaml", "--word_file", word_file_path], check=True)
        print(f"layout_detection.py finished successfully for {pdf_file_path}.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running layout_detection.py for {pdf_file_path}: {e}")
        sys.exit(1)  # Exit the script if layout_detection.py fails

def process_pdfs_in_directory(pdf_dir_path, word_file_path):
    """
    Process all PDFs in the specified directory.
    """
    # Get all PDF files from the directory
    pdf_files = [f for f in os.listdir(pdf_dir_path) if f.lower().endswith('.pdf')]

    for pdf_file in pdf_files:
        pdf_file_path = os.path.join(pdf_dir_path, pdf_file)
        print(f"Processing PDF: {pdf_file_path}")

        # Run askgpt.py
        run_askgpt(word_file_path, pdf_file_path)

        # Run layout_detection.py
        run_layout_detection(word_file_path, pdf_file_path)

def clean_up_output_directory(output_dir_path):
    """
    Delete all files in the specified output directory.
    """
    try:
        for filename in os.listdir(output_dir_path):
            file_path = os.path.join(output_dir_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)  # Delete file
                print(f"Deleted file: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Delete directory and its contents
                print(f"Deleted directory: {file_path}")
    except Exception as e:
        print(f"Error cleaning up output directory: {e}")

def main():
    """
    Main function to process all PDFs in the folder and clean up the output directory.
    """
    # Run the process for all PDFs in the directory
    process_pdfs_in_directory(PDF_DIR_PATH, WORD_FILE_PATH)

    # Clean up the output directory after processing all PDFs
    clean_up_output_directory(OUTPUT_DIR_PATH)

if __name__ == "__main__":
    main()
