# -*- coding: utf-8 -*-
# Suqi 20250117
import os
import PyPDF2
import pandas as pd
from openai import OpenAI
import tiktoken
import re

current_dir = os.path.dirname(os.path.abspath(__file__))

# Extract text from PDF
def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text

# Clean PDF text by removing empty lines and unnecessary spaces
def clean_pdf_text(text):
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned_lines)

# Extract DOI from text using regex
def extract_doi(text):
    doi_pattern = r'10\.[\d]{4,9}/[-._;()/:A-Z0-9]+'  # Regex for DOI
    match = re.search(doi_pattern, text, re.IGNORECASE)
    return match.group(0) if match else "DOI 未找到"

# Count the tokens in the text
def count_tokens(text):
    try:
        encoding = tiktoken.get_encoding("cl100k_base")  # Use OpenAI's compatible tokenizer
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error in token counting: {e}")
        return 0

# Split the text into chunks based on the token limit
def split_text_into_chunks(text, max_tokens=55000):
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = encoding.decode(tokens[i:i + max_tokens])
        chunks.append(chunk)
    return chunks

# Analyze the chunks with OpenAI's GPT model
def analyze_chunks_with_openai(chunks, client):
    results = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "请提取文件中的氧化还原电势信息，包括氧化电位和还原电位，对应上每一个化合物名称（包括全称和简称）和结构式以及CCDC编号（请只写数字即可），并且标明测量时候的溶剂和参比电极;请将搜索到的东西按照以下格式输出：1. 化合物简称：2. 化合物全称：3. 结构式：4. 氧化电势：5. 还原电势：6. 溶剂：7. 参比电极：8. CCDC编号：，如有多个化合物，请按照顺序输出，用换行符隔开。并且将可能表示上述化合物结构的图片代号也一并输出（类似于Scheme 1,Figure 2,Table 3等），写在9. 图片代号：后面，如果没有就写未提供"},
                    {"role": "user", "content": chunk}
                ],
                max_tokens=8192,
                temperature=0.7,
                stream=False
            )
            # check if the response is valid
            if hasattr(response, "choices") and len(response.choices) > 0:
                results.append(response.choices[0].message.content)
            else:
                raise ValueError("Invalid response format from API")
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
    return results

# Save the combined results to an Excel file
def save_combined_excel(file_path, combined_data):
    columns_to_keep = [
        "Index", "File Name", "DOI", "1. 化合物简称", "2. 化合物全称", "3. 结构式", "4. 氧化电势",
        "5. 还原电势", "6. 溶剂", "7. 参比电极", "8. CCDC编号", "9. 图片代号"
    ]
    df = pd.DataFrame(combined_data)
    df = df[columns_to_keep]  # Keep only specified columns
    df.to_excel(file_path, index=False, engine='openpyxl')  # Save as Excel file using openpyxl
    print(f"Combined analysis saved to {file_path}")

# Initialize OpenAI client
client = OpenAI(
    api_key="sk-95a69b075eb84e9e93efa658892c5474",  # Replace with your API Key
    base_url="https://api.deepseek.com"  # Use the DeepSeek provided OpenAI compatible API endpoint
)

# Process all PDFs in a folder and save to one Excel file
def process_folder(folder_path, output_file):
    combined_data = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {file_name}")
            pdf_text = extract_text_from_pdf(file_path)
            pdf_text = clean_pdf_text(pdf_text)

            # Check if "voltammetry" is in the text (case insensitive)
            if "voltammetry" in pdf_text.lower().replace(" ", ""):
                # Extract DOI
                doi = extract_doi(pdf_text)
                print(f"Extracted DOI for {file_name}: {doi}")

                # Count tokens in the text
                token_count = count_tokens(pdf_text)
                print(f"The text contains {token_count} tokens.")

                # Split text into chunks
                pdf_chunks = split_text_into_chunks(pdf_text, max_tokens=55000)

                # Analyze each chunk
                chunk_results = analyze_chunks_with_openai(pdf_chunks, client)

                # Combine results for the file
                for result in chunk_results:
                    for block in result.split("\n\n"):
                        lines = block.split("\n")
                        entry = {"File Name": file_name, "DOI": doi}
                        oxidation_potential_present = False
                        reduction_potential_present = False

                        for line in lines:
                            if line.strip() and "：" in line:  # Ensure the line contains a valid key-value pair
                                key, value = line.split("：", 1)
                                value = value.strip()
                                # Check for numeric data in oxidation or reduction potentials
                                if key.strip() == "4. 氧化电势" and any(char.isdigit() for char in value):
                                    oxidation_potential_present = True
                                if key.strip() == "5. 还原电势" and any(char.isdigit() for char in value):
                                    reduction_potential_present = True
                                entry[key.strip()] = value

                        # Append entry only if oxidation or reduction potential is present
                        if oxidation_potential_present or reduction_potential_present:
                            combined_data.append(entry)
            else:
                print(f"Skipping file {file_name} as 'voltammetry' was not found in the content.")

    # Ensure all rows are properly aligned in the Excel
    columns_to_keep = [
        "File Name", "DOI", "1. 化合物简称", "2. 化合物全称", "3. 结构式", "4. 氧化电势",
        "5. 还原电势", "6. 溶剂", "7. 参比电极", "8. CCDC编号", "9. 图片代号"
    ]
    df = pd.DataFrame(combined_data)
    df = df.reindex(columns=columns_to_keep, fill_value="")  # Reindex and fill missing columns

    # Add a new sequential index column
    df.insert(0, "Index", range(1, len(df) + 1))  # Add a new sequential Index column starting from 1

    # Save to Excel
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"Combined analysis saved to {output_file}")

# Define folder path and output file
input_folder = os.path.join(current_dir, "dAu_pdf")
output_file = os.path.join(current_dir, "final_results.xlsx")

# Process all PDFs in the input folder and save to one Excel file
process_folder(input_folder, output_file)
