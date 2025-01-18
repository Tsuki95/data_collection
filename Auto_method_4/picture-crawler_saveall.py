# -*- coding: utf-8 -*-
# Suqi 20250117
import os
import re
import argparse
from docx import Document
from docx.shared import Inches
from markdown import markdown
from bs4 import BeautifulSoup
from pylatexenc.latex2text import LatexNodes2Text

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)


# Ensure directory exists
def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)  # Create the directory


# Extract image identifiers from redox_analysis_filtered.txt
def extract_image_identifiers(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
        matches = re.findall(r"图片代号：(.+)", text)
        image_identifiers = []
        for match in matches:
            image_identifiers.extend([identifier.strip() for identifier in match.split(",")])
        return set(image_identifiers)


# Extract relevant sections from Markdown text
def extract_related_sections(markdown_text, image_identifiers):
    lines = markdown_text.splitlines()
    extracted_sections = []

    for i, line in enumerate(lines):
        if ".jpg" in line:
            matched_lines = []

            for j in range(max(0, i - 1), i):
                if re.match(r"^(Scheme|Figure|Table)", lines[j], re.IGNORECASE):
                    start_index = j
                    while start_index < len(lines) and lines[start_index].strip() != "":
                        matched_lines.append(lines[start_index])
                        start_index += 1
                    break

            matched_lines.append(line)

            for j in range(i + 1, min(i + 2, len(lines))):
                if re.match(r"^(Scheme|Figure|Table)", lines[j], re.IGNORECASE):
                    start_index = j
                    while start_index < len(lines) and lines[start_index].strip() != "":
                        matched_lines.append(lines[start_index])
                        start_index += 1
                    break

            full_text = "\n".join(matched_lines)
            if any(identifier in full_text for identifier in image_identifiers):
                extracted_sections.append(full_text)

    return extracted_sections


# Convert Markdown and LaTeX to human-readable text
def markdown_to_readable_text(markdown_text):
    html = markdown(markdown_text)
    soup = BeautifulSoup(html, "html.parser")
    plain_text = soup.get_text()
    plain_text = LatexNodes2Text().latex_to_text(plain_text)
    plain_text = re.sub(r"\s+\n", "\n", plain_text)
    plain_text = re.sub(r"\n\s+", "\n", plain_text)
    plain_text = re.sub(r"\n{2,}", "\n\n", plain_text)
    return plain_text.strip()


# Insert summary content into Word document
def insert_summary_to_docx(summary_file, docx_file):
    # Create a new document if it doesn't exist
    if not os.path.exists(docx_file):
        doc = Document()
    else:
        doc = Document(docx_file)

    # Read the summary file content
    with open(summary_file, "r", encoding="utf-8") as file:
        summary_text = file.read()

    # Insert the summary content
    doc.add_paragraph("openai总结内容：")
    doc.add_paragraph(summary_text)
    doc.add_paragraph("---------------------")

    # Save the document
    doc.save(docx_file)
    print(f"总结内容已插入到 {docx_file}")


def append_images_and_text_to_docx(results, docx_file, output):
    # Open the existing Word document
    doc = Document(docx_file)

    # Add a heading for the images
    doc.add_paragraph("相关图片：", style="Heading 2")

    for section in results:
        # Extract image paths
        img_matches = re.findall(r"!\[.*?\]\((.*?)\)", section)
        print("图片路径匹配结果:", img_matches)
        text_without_images = re.sub(r"!\[.*?\]\(.*?\)", "", section).strip()
        readable_text = markdown_to_readable_text(text_without_images)

        # Add explanatory text
        if readable_text:
            doc.add_paragraph(readable_text)

        # Insert images
        for img_path in img_matches:
            img_path = img_path.strip()
            img_path = os.path.join(output, img_path)  # Use output as the base path
            if os.path.exists(img_path):
                try:
                    doc.add_picture(img_path, width=Inches(4.0))
                    print(f"检查图片路径: {img_path} - 存在: {os.path.exists(img_path)}")
                except Exception as e:
                    print(f"无法加载图片 {img_path}: {e}")

        doc.add_paragraph("-------------------------------")

    # Save the document
    doc.save(docx_file)
    print(f"图片和说明已保存到 {docx_file}")


# Main process
if __name__ == "__main__":
    # Add command line arguments
    parser = argparse.ArgumentParser(description="Process Markdown and TXT into Word")
    parser.add_argument("--output_txt", required=True, help="Path to the redox_analysis_filtered.txt file")
    parser.add_argument("--markdown_file_path", required=True, help="Path to the markdown file")
    parser.add_argument("--output_docx_path", required=True, help="Path to the output Word document")
    parser.add_argument("--output", required=True, help="Base directory for output")
    args = parser.parse_args()

    # Path parameters
    output_txt = args.output_txt
    markdown_file_path = args.markdown_file_path
    final_docx_path = args.output_docx_path
    output = args.output

    # Ensure the directory exists
    ensure_directory_exists(final_docx_path)

    # Extract image identifiers
    image_identifiers = extract_image_identifiers(output_txt)
    print(image_identifiers)

    # Read the Markdown file
    with open(markdown_file_path, 'r', encoding='utf-8') as file:
        markdown_text = file.read()

    # Extract related sections
    results = extract_related_sections(markdown_text, image_identifiers)
    print("提取到的相关段落:", results)

    # Insert summary content into the document
    insert_summary_to_docx(output_txt, final_docx_path)

    # Append images and explanations to the document
    append_images_and_text_to_docx(results, final_docx_path, output)

    print(f"最终文档已保存到 {final_docx_path}")