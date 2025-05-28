# -*- coding: utf-8 -*-
# Suqi 20250117
import asyncio
from playwright.async_api import async_playwright
from langchain_community.document_transformers import Html2TextTransformer
from langchain_core.documents import Document
from openai import OpenAI
import pandas as pd
import os

import nest_asyncio
nest_asyncio.apply()

current_dir = os.path.dirname(os.path.abspath(__file__))

# Function to save text content to a file
def save_to_txt_file(content, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Text content saved to {file_path}")

# Function to split text into chunks based on token limit
def split_text_into_chunks(text, max_tokens=128000):
    import tiktoken
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = encoding.decode(tokens[i:i + max_tokens])
        chunks.append(chunk)
    return chunks

# Function to analyze text chunks using GPT-4
def analyze_chunks_with_gpt4(chunks, client):
    results = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "请提取文件中的氧化还原电势信息，包括氧化电位和还原电位，对应上每一个化合物名称（包括全称和简称）和结构式以及CCDC编号（仅写数字不写链接），并且标明测量时候的溶剂和参比电极;请将搜索到的东西按照以下格式输出：1. 化合物简称：2. 化合物全称：3. 结构式：4. 氧化电势：5. 还原电势：6. 溶剂：7. 参比电极：8. CCDC编号：，如有多个化合物，请按照顺序输出，用换行符隔开。并且将可能表示上述化合物结构的图片代号也一并输出（类似于Scheme 1,Figure 2,Table 3等），写在9. 图片代号：后面，如果没有就写未提供"},
                    {"role": "user", "content": chunk}
                ]
            )
            result = response.choices[0].message.content
            results.append(result)
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
    return results

# Function to save combined data to a CSV file
def save_combined_csv(file_path, combined_data):
    """
    保存分析结果到 CSV 文件。

    Args:
        file_path (str): CSV 文件路径。
        combined_data (list): 分析结果数据。
    """
    filtered_data = []
    for entry in combined_data:
        oxidation_potential = entry.get("4. 氧化电势", "")
        reduction_potential = entry.get("5. 还原电势", "")

        # Check if the entry contains any digits
        if any(char.isdigit() for char in oxidation_potential) or any(char.isdigit() for char in reduction_potential):
            filtered_data.append(entry)

    # Convert to Pandas DataFrame
    df = pd.DataFrame(filtered_data)

    # Add an index column
    df.insert(0, "Index", range(1, len(df) + 1))

    # Save to CSV file
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"Filtered analysis saved to {file_path}")

# Main function to fetch and analyze data from a csv file
async def fetch_and_analyze_from_csv(input_csv, url_column, txt_output_folder, csv_output_file):
    client = OpenAI(
        api_key="sk-J1swmxizRQVJuMtk9mCcx7eUaFCZQeNdLEGIe5iW1szAuagE",  # 替换为你的 GPT-4 API Key
        base_url="https://api.chatanywhere.tech/v1"  # 替换为 GPT-4 API 的地址
    )

    # Read the csv file
    df = pd.read_csv(input_csv)
    urls = df[url_column].dropna().tolist()

    combined_results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Launch browser in non-headless mode
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )

        page = await context.new_page()
        page.set_default_navigation_timeout(60000)  # Set navigation timeout

        for url in urls:
            print(f"Navigating to {url}...")
            try:
                await page.goto(url, timeout=60000)
                html_content = await page.content()
                print(f"Content from {url} retrieved successfully.")

                # Convert HTML to plain text using Html2TextTransformer
                transformer = Html2TextTransformer(ignore_links=False)
                document = Document(page_content=html_content, metadata={"source": url})
                transformed_docs = transformer.transform_documents([document])
                text_content = transformed_docs[0].page_content

                # Save plain text content to a file
                txt_file_path = os.path.join(txt_output_folder, f"{url.replace(':', '_').replace('/', '_')}.txt")
                save_to_txt_file(text_content, txt_file_path)

                # Check if the text contains "voltammetry"
                if "voltammetry" in text_content.lower().replace(" ", ""):
                    print("'voltammetry' found. Proceeding with analysis...")

                    # Split text into chunks
                    chunks = split_text_into_chunks(text_content)

                    # Analyze text chunks
                    analysis_results = analyze_chunks_with_gpt4(chunks, client)

                    # Process analysis results
                    for result in analysis_results:
                        for block in result.split("\n\n"):
                            lines = block.split("\n")
                            entry = {"URL": url}
                            for line in lines:
                                if line.strip() and "：" in line:
                                    key, value = line.split("：", 1)
                                    entry[key.strip()] = value.strip()
                            combined_results.append(entry)
                else:
                    print("'Cyclic voltammetry' not found in the content.")

            except Exception as e:
                print(f"Error navigating to {url}: {e}")

        await browser.close()

    # Save results to csv
    save_combined_csv(csv_output_file, combined_results)

if __name__ == "__main__":
    input_csv = os.path.join(current_dir, "molecule_doi_info.csv")  # csv file containing URLs
    url_column = "url"  # Column name containing URLs
    txt_output_folder = os.path.join(current_dir, "txt_outputs")  # Folder to save plain text content
    csv_output_file = os.path.join(current_dir, "final_results.csv") # CSV file to save analysis results

    os.makedirs(txt_output_folder, exist_ok=True)

    asyncio.run(fetch_and_analyze_from_csv(input_csv, url_column, txt_output_folder, csv_output_file))
