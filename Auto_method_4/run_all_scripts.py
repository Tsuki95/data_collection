# -*- coding: utf-8 -*-
# Suqi 20250117
import subprocess
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) # 获取当前脚本所在的目录
pdf_dir = os.path.join(current_dir, "pdf") # pdf文件夹路径

os.makedirs(pdf_dir, exist_ok=True)

for pdf_file in os.listdir(pdf_dir):
    if pdf_file.lower().endswith('.pdf'):
        # Configure paths
        pdf_filename_no_ext = os.path.splitext(pdf_file)[0]
        
        output = os.path.join(current_dir, "outputs", pdf_filename_no_ext) # 输出文件夹路径
        os.makedirs(output, exist_ok=True) # Ensure the output directory exists
        
        pdf_path = os.path.join(pdf_dir, pdf_file)
        output_txt = os.path.join(output, "redox_analysis.txt")
        image_dir = os.path.join(output, "img_markdown")
        markdown_dir = os.path.join(output, "md_markdown")
        markdown_file_path = os.path.join(markdown_dir, f"{pdf_filename_no_ext}.md")
        output_docx_path = os.path.join(output, "final_extracted_images_and_text.docx")

        # Ensure the output directories exist
        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(markdown_dir, exist_ok=True)

        askgpt_script = os.path.join(current_dir, "askgpt.py")
        pdf2markdown_script = os.path.join(current_dir, "pdf2markdown.py")
        picture_crawler_script = os.path.join(current_dir, "picture-crawler_saveall.py")

        try:
            print(f"正在处理: {pdf_file}")
            
            # Run askgpt.py
            subprocess.run(["python", 
                          askgpt_script,
                          "--pdf_path", pdf_path,
                          "--output_txt", output_txt
                          ], check=True)

            # Run pdf2markdown.py
            subprocess.run([
                "python",
                pdf2markdown_script,
                "--pdf_path", pdf_path,
                "--image_dir", image_dir,
                "--markdown_dir", markdown_dir
            ], check=True)
            
            # Run picture-crawler_saveall.py
            subprocess.run([
                "python",
                picture_crawler_script,
                "--output_txt", output_txt,
                "--markdown_file_path", markdown_file_path,
                "--output_docx_path", output_docx_path,
                "--output", output
            ], check=True)
            
            print(f"完成处理: {pdf_file}")
            
        except subprocess.CalledProcessError as e:
            print(f"处理 {pdf_file} 时出错: {e}")
        except Exception as e:
            print(f"处理 {pdf_file} 时发生意外错误: {e}")
