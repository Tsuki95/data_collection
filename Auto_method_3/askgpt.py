# -*- coding: utf-8 -*-
# Suqi 20250117
import os
import PyPDF2
import docx
import argparse
from openai import OpenAI
import tiktoken

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
def split_text_into_chunks(text, max_tokens=128000):
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
                    {"role": "system", "content": "请提取文件中的氧化还原电势信息，包括氧化电位和还原电位，对应上每一个化合物名称（包括全称和简称）和结构式以及CCDC编号（仅输出数字），并且标明测量时候的溶剂和参比电极;请将搜索到的东西按照以下格式输出：1.化合物简称：2. 化合物全称：3.氧化电势：4.还原电势：5.溶剂：6.参比电极：7.结构式：8.CCDC编号：，如有多个化合物，请按照顺序输出，用换行符隔开。并且将可能表示上述化合物结构的图片代号也一并输出（类似于Scheme 1,Figure 2,Table 3等），写在9.图片代号：后面，如果没有就写未提供"},
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
        if not any(keyword in result for keyword in ["对不起", "抱歉", "没有提供", "并未提供", "无法提取", "未给出", "没有", "并不在"]):  # Check if it contains invalid keywords
            filtered_results.append(result)
    return filtered_results

# save results to Word
def save_to_word(file_path, content):
    doc = docx.Document()
    doc.add_heading("氧化还原电势信息：", level=2)  # Add a heading
    doc.add_paragraph(content)   # Add content
    doc.add_paragraph("\n--------------------------------------------------------------------")  # Add a separator line
    doc.save(file_path)
    print(f"Analysis saved to {file_path}")

def main(word_path, pdf_path):
    # API Key
    client = OpenAI(
        api_key="sk-J1swmxizRQVJuMtk9mCcx7eUaFCZQeNdLEGIe5iW1szAuagE",  # 替换为你的 API Key
        base_url="https://api.chatanywhere.tech/v1"
    )

    # PDF plain text
    pdf_text = extract_text_from_pdf(pdf_path)
    pdf_text = clean_pdf_text(pdf_text)

    # set to chunks
    pdf_chunks = split_text_into_chunks(pdf_text)

    # analyse each chunk
    analysis_results = analyze_chunks_with_gpt4(pdf_chunks, client)

    # filter invalid results
    filtered_results = filter_invalid_responses(analysis_results)

    # join all results
    final_analysis = "\n\n".join(filtered_results)

    # save to Word
    save_to_word(word_path, final_analysis)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run askgpt.py to analyze PDF text and save results to Word file.")
    parser.add_argument("--word_file", type=str, required=True, help="Path to save the Word file")
    parser.add_argument("--pdf_file", type=str, required=True, help="Path to the PDF file to analyze")
    args = parser.parse_args()

    main(word_path=args.word_file, pdf_path=args.pdf_file)




