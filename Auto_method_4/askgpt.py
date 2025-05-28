# -*- coding: utf-8 -*-
# Suqi 20250117
import PyPDF2
from openai import OpenAI
import tiktoken
import os
import argparse

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)

# extract PDF
def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text

# clean PDF
def clean_pdf_text(text):
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned_lines)

# cleavage PDF
def split_text_into_chunks(text, max_tokens=125000):
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = encoding.decode(tokens[i:i + max_tokens])
        chunks.append(chunk)
    return chunks

# analyse chunk
def analyze_chunks_with_gpt4(chunks, client):
    results = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "请提取文件中的氧化还原电势信息，包括氧化电位和还原电位，对应上每一个化合物名称（包括全称和简称）和结构式以及CCDC编号，并且标明测量时候的溶剂和参比电极;请将搜索到的东西按照以下格式输出：1.化合物简称：2. 化合物全称：3.氧化电势：4.还原电势：5.溶剂：6.参比电极：7.结构式：8.CCDC编号：，如有多个化合物，请按照顺序输出，用换行符隔开。并且将可能表示上述化合物的图片代号也一并输出（Scheme,Figure,Table等），写在9.图片代号：后面"},
                    {"role": "user", "content": chunk}
                ]
            )
            # check if the response is valid
            if hasattr(response, "choices"):
                result = response.choices[0].message.content
            else:
                raise ValueError("Invalid response format from API")
            results.append(result)
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
    return results

# filter invalid texts
def filter_invalid_responses(results):
    filtered_results = []
    for result in results:
        if not any(keyword in result for keyword in ["对不起", "抱歉", "没有提供", "并未提供", "无法提取", "未给出", "没有", "并不在"]):  # Check if the result contains invalid keywords
            filtered_results.append(result)
    return filtered_results

# API Key
client = OpenAI(
    api_key="sk-J1swmxizRQVJuMtk9mCcx7eUaFCZQeNdLEGIe5iW1szAuagE",  # 替换为你的 API Key
    base_url="https://api.chatanywhere.tech/v1"
)


# Main process
if __name__ == "__main__":
    # Add command line arguments
    parser = argparse.ArgumentParser(description="Process PDF and output analysis")
    parser.add_argument("--pdf_path", required=True, help="Path to the PDF file")
    parser.add_argument("--output_txt", required=True, help="Path to the output text file")
    args = parser.parse_args()

    # Get paths from command line arguments
    pdf_path = args.pdf_path
    output_txt = args.output_txt

    # Extract PDF content
    pdf_text = extract_text_from_pdf(pdf_path)
    pdf_text = clean_pdf_text(pdf_text)

    # Split into chunks
    pdf_chunks = split_text_into_chunks(pdf_text)

    # Analyze chunks
    analysis_results = analyze_chunks_with_gpt4(pdf_chunks, client)

    # Filter invalid results
    filtered_results = filter_invalid_responses(analysis_results)

    # Combine and save results
    final_analysis = "\n\n".join(filtered_results)
    with open(output_txt, "w", encoding="utf-8") as file:
        file.write(final_analysis)
    print(f"Analysis saved to {output_txt}")