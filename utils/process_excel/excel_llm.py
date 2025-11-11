import json
import os
from typing import List

from config.config import LAYOUT_IDENTIFY_PROMPT, HEADER_ROW_DETECTION_PROMPT, CORRECTION_PROMPT, \
    EXCEL_TABLE_EXTRACTION_PROMPT
from dashscope import MultiModalConversation, Generation
from dotenv import load_dotenv

load_dotenv()

# Excel 布局检测
def detect_excel_layout(file_paths: List[str]) -> dict:
    content = []
    for file_path in file_paths:
        content.append({"image": file_path})
    content.append({"text": LAYOUT_IDENTIFY_PROMPT})
    messages = [
        {
            "role": "user",
            "content": content,
        }
    ]
    response = MultiModalConversation.call(
        api_key=os.getenv("DASHSCOPE_API_KEY1"),
        model="qwen3-vl-plus",
        messages=messages,
    )
    return response.get("output").choices[0].get("message").get("content")[0].get("text")

# 判断读取前20行数据的表头索引
def determine_header_index(rows):
    rows_str = json.dumps(rows, ensure_ascii=False)
    print(rows_str)
    messages = [
        {"role": "system", "content": HEADER_ROW_DETECTION_PROMPT},
        {"role": "user", "content": rows_str},
    ]
    response = Generation.call(
        api_key=os.getenv("DASHSCOPE_API_KEY2"),
        model="qwen3-max",
        messages=messages,
        result_format="message",
        enable_thinking=False,
    )
    return response.get("output").choices[0].get("message").get("content")

# 纠正表格
def correct_excel_table(file_paths: List[str], markdown_content: str) -> dict:
    content = []
    for file_path in file_paths:
        content.append({"image": file_path})
    content.append({"text": markdown_content})
    content.append({"text": CORRECTION_PROMPT})
    messages = [
        {
            "role": "user",
            "content": content,
        }
    ]
    response = MultiModalConversation.call(
        api_key=os.getenv("DASHSCOPE_API_KEY2"),
        model="qwen3-vl-plus",
        messages=messages,
    )
    return response.get("output").choices[0].get("message").get("content")[0].get("text")

# 提取图片的数据输出markdown
def extract_excel_data_to_markdown(file_paths: List[str]) -> dict:
    content = []
    for file_path in file_paths:
        content.append({"image": file_path})
    content.append({"text": EXCEL_TABLE_EXTRACTION_PROMPT})
    messages = [
        {
            "role": "user",
            "content": content
        }
    ]
    response = MultiModalConversation.call(
        api_key=os.getenv("DASHSCOPE_API_KEY2"),
        model="qwen3-vl-plus",
        messages=messages,
    )
    return response.get("output").choices[0].get("message").get("content")[0].get("text")

if __name__ == "__main__":
    file_paths = [
        './img/Sheet.png',
        './img/Sheet1.png',
        './img/Sheet1 (2).png',
    ]
    res = detect_excel_layout(file_paths)
    print(res)
