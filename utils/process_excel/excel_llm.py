import json
import os
from typing import List

from config.config import LAYOUT_DETECTION_PROMPT, HEADER_ROW_DETECTION_PROMPT, CORRECTION_PROMPT
from dashscope import MultiModalConversation, Generation
from dotenv import load_dotenv

load_dotenv()

# Excel 布局检测
def detect_excel_layout(file_path: str) -> dict:
    messages = [
        {
            "role": "user",
            "content": [{"image": file_path}, {"text": LAYOUT_DETECTION_PROMPT}],
        }
    ]
    response = MultiModalConversation.call(
        api_key=os.getenv("DASHSCOPE_API_KEY2"),
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

if __name__ == "__main__":
    print('测试 Excel 布局检测')
    temp = """
    ```markdown
| 项目        | 内容                         |
|-------------|------------------------------|
| 船代公司    | 浙江中外运有限公司宁波物流分公司 |
| 外销合同号  | N25MU05001                   |

### 费用明细：
| 费用名称     | 币种 | 金额 | 备注         |
|--------------|------|------|--------------|
| 订舱费       | RMB  | 200  |              |
| THC          | RMB  | 685  |              |
| 文件费       | RMB  | 450  |              |
| EDI          | RMB  | 10   |              |
| 电子装箱单费 | RMB  | 10   |              |
| 箱单费       | RMB  | 60   |              |
| 堆存费       | RMB  | 12   |              |
| 电放费       | RMB  | 300  |              |
| 拖卡费       | RMB  | 1975 | 安吉梅溪      |
| 吊机费       | RMB  | 30   |              |
| 报关费       | RMB  | 100  |              |
| 合计         | RMB  | 3832 |              |
```
    """
    res = correct_excel_table(['../../converted_files/excel_work/images/output.png'], temp)
    print(res)
