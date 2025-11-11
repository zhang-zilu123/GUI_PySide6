import json
import os
import time

from typing import List

from config.config import LAYOUT_IDENTIFY_PROMPT, HEADER_ROW_DETECTION_PROMPT, CORRECTION_PROMPT, \
    EXCEL_TABLE_EXTRACTION_PROMPT
from dashscope import MultiModalConversation, Generation
from dotenv import load_dotenv

load_dotenv()

# Excel 布局检测
def detect_excel_layout(file_paths: List[str]) -> dict:
    print('detect_excel_layout', file_paths[0])
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
def correct_excel_table(file_paths: List[str], markdown_content: str) -> str:
    content = []
    for file_path in file_paths:
        content.append({"image": file_path})
    content.append({"text": markdown_content})
    content.append({"text": CORRECTION_PROMPT})
    enable_thinking = True

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
        stream=True,
        enable_thinking=enable_thinking,
        thinking_budget=81920,
    )
    # print('correction response:', response)
    # 定义完整思考过程
    reasoning_content = ""
    # 定义完整回复
    answer_content = ""
    # 判断是否结束思考过程并开始回复
    is_answering = False
    if enable_thinking:
        print("=" * 20 + "思考过程" + "=" * 20)

    for chunk in response:
        # 如果思考过程与回复皆为空，则忽略
        message = chunk.output.choices[0].message
        reasoning_content_chunk = message.get("reasoning_content", None)
        if (chunk.output.choices[0].message.content == [] and
                reasoning_content_chunk == ""):
            pass
        else:
            # 如果当前为思考过程
            if reasoning_content_chunk != None and chunk.output.choices[0].message.content == []:
                # print(chunk.output.choices[0].message.reasoning_content, end="")
                reasoning_content += chunk.output.choices[0].message.reasoning_content
            # 如果当前为回复
            elif chunk.output.choices[0].message.content != []:
                if not is_answering:
                    print("\n" + "=" * 20 + "完整回复" + "=" * 20)
                    is_answering = True
                print(chunk.output.choices[0].message.content[0]["text"], end="")
                answer_content += chunk.output.choices[0].message.content[0]["text"]
    # return response.get("output").choices[0].get("message").get("content")[0].get("text")

# 提取图片的数据输出markdown
def extract_excel_data_to_markdown(file_paths: List[str]) -> str:
    content = []
    print("file_paths:", file_paths[0])
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
    with open('output.md', 'r', encoding='utf-8') as f:
        md_content = f.read()

    file_path = ['./imgs/Sheet_rows_1_to_40.png',
                 './imgs/Sheet_rows_41_to_80.png',
                 './imgs/Sheet_rows_81_to_120.png',
                 './imgs/Sheet_rows_121_to_160.png',
                 './imgs/Sheet_rows_161_to_178.png', ]
    # 计时开始
    start_time = time.time()
    correct_excel_table(file_path, md_content)
    # 计时结束
    end_time = time.time()
    print(f"函数运行时间: {end_time - start_time:.4f} 秒")
