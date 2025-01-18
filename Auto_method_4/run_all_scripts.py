# -*- coding: utf-8 -*-
# Suqi 20250117
import subprocess
import os

# Configure paths
output = r"E:\\crawler\\autocrawler\\outputs"  # 写入输出文件的目录
pdf_path = r"E:\\crawler\\dAu_cyclic_volt\\zayakin-et-al-2022-au-au-chemical-bonding-in-nitronyl-nitroxide-gold(i)-derivatives.pdf"  # PDF文件的路径

pdf_filename_no_ext = os.path.splitext(os.path.basename(pdf_path))[0]

output_txt = f"{output}\\redox_analysis.txt"
image_dir = f"{output}\\img_markdown"
markdown_dir = f"{output}\\md_markdown"
markdown_file_path = f"{markdown_dir}\\{pdf_filename_no_ext}.md"
output_docx_path = f"{output}\\final_extracted_images_and_text.docx"

# Ensure the output directories exist
os.makedirs(output, exist_ok=True)
os.makedirs(f"{output}\\img_markdown", exist_ok=True)
os.makedirs(f"{output}\\md_markdown", exist_ok=True)

# Run askgpt.py
subprocess.run(["python", 
                "E:/crawler/autocrawler/askgpt.py",
                "--pdf_path", pdf_path,
                "--output_txt", output_txt
], check=True)

# Run pdf2markdown.py
subprocess.run([
    "python",
    "E:/crawler/autocrawler/pdf2markdown.py",
    "--pdf_path", pdf_path,
    "--image_dir", image_dir,
    "--markdown_dir", markdown_dir
], check=True)
 
# Run picture-crawler_saveall.py
subprocess.run([
    "python",
    "E:/crawler/autocrawler/picture-crawler_saveall.py",
    "--output_txt", output_txt,
    "--markdown_file_path", markdown_file_path,
    "--output_docx_path", output_docx_path,
    "--output", output
], check=True)
