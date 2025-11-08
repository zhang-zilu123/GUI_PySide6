"""
Markdown文件信息提取模块
使用AI模型从Markdown文件中提取费用明细信息
"""
import os
from typing import Optional
from random import choice

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# API密钥池
DASH_KEYS = [
    os.getenv("DASHSCOPE_API_KEY1"),
    os.getenv("DASHSCOPE_API_KEY2"),
    os.getenv("DASHSCOPE_API_KEY3"),
]

def extract_info_from_md(md_file_path: str) -> str:
    """从单个markdown文件中提取信息
    
    Args:
        md_file_path: Markdown文件路径
        
    Returns:
        提取的JSON字符串结果
        
    Raises:
        FileNotFoundError: 当文件不存在时
        Exception: 当API调用失败时
    """
    content = _read_markdown_file(md_file_path)
    if not content:
        return "{}"

    try:
        client = _create_openai_client()
        response = _call_extraction_api(client, content)
        return response.choices[0].message.content

    except Exception as e:
        print(f"API调用失败: {e}")
        raise

def _read_markdown_file(file_path: str) -> Optional[str]:
    """读取Markdown文件内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容或None（如果读取失败）
    """
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在。")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None

def _create_openai_client() -> OpenAI:
    """创建OpenAI客户端
    
    Returns:
        配置好的OpenAI客户端
    """
    return OpenAI(
        api_key=choice(DASH_KEYS),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

def _call_extraction_api(client: OpenAI, content: str):
    """调用信息提取API
    
    Args:
        client: OpenAI客户端
        content: 要处理的内容
        
    Returns:
        API响应
    """
    prompt = _build_extraction_prompt(content)

    return client.chat.completions.create(
        model="qwen-max",
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant designed to output JSON.'},
            {'role': 'user', 'content': prompt}
        ],
        response_format={"type": "json_object"}
    )

def _build_extraction_prompt(content: str) -> str:
    """构建提取信息的提示词
    
    Args:
        content: 文档内容
        
    Returns:
        完整的提示词
    """
    # 简化的提示词，避免复杂的格式问题
    prompt = """你是一个专业的物流费用数据提取专家。你的任务是从 Markdown 格式的费用单中提取信息，并输出纯 JSON 格式。

    <重要>你的回复必须是纯 JSON 格式，不允许有任何其他内容</重要>

    ## 输出格式（必须严格遵守）

    你必须输出一个 JSON 对象，格式如下：
    ```json
    {
        "费用明细": [
            {
                "外销合同": "字符串",
                "船代公司": "字符串",
                "费用名称": "字符串",
                "货币代码": "字符串",
                "金额": "字符串",
                "备注": "字符串"
            }
        ]
    }
    ```

    ## 输出要求（违反将视为失败）

    1. 只输出 JSON，不要输出任何解释、说明、思考过程
    2. 不要使用 Markdown 代码块标记（不要用 ```json 或 ```）
    3. 不要在 JSON 前后添加任何文字
    4. 所有字段值都是字符串类型，包括金额
    5. 缺失的字段用空字符串 "" 填充
    6. 金额保留两位小数，格式如 "123.45"

    ## 字段提取规则

    ### 1. 外销合同
    从文档中查找以下关键词对应的值：
    - 委托编号、业务编号、合同号、工作单号、订舱号、提单号、编号
    - 格式通常为：字母+数字组合（如 SEAE25090135、D25DW02025B、ZIMUGZH0603587）
    - 优先选择文档开头或表格中重复出现的编号

    ### 2. 船代公司
    识别提供物流服务的公司，通常在文档标题或账户信息处：
    - **优先识别**：包含"物流"、"船务"、"货运"、"航运"、"船代"、"供应链"等关键词的公司
    - **次要识别**：出现在银行账户信息区域的公司名称
    - **排除**：标注为"委托方"、"货主"的公司，或纯"贸易"、"进出口"公司

    ### 3. 费用名称
    从表格中提取费用项目名称：
    - 去除行首编号（如 "1." "2."）
    - 去除货币符号和括号（如 "场站费 (￥)" → "场站费"）
    - 保留完整的费用描述（如 "VGM 411漏收"）
    - 忽略"合计"、"小计"、"总计"等汇总行

    ### 4. 货币代码
    根据金额所在列或货币符号判断：
    - ￥ 或 RMB → CNY
    - $ 或 USD → USD  
    - HKD → HKD
    - EUR → EUR
    - JPY → JPY

    ### 5. 金额
    提取每行费用的合计金额（不是单价）：
    - 去除货币符号（￥、$）
    - 去除千分位逗号（6,810.00 → 6810.00）
    - 去除空格
    - 保留两位小数（800 → 800.00）
    - 空值或"-"用 "0.00" 表示
    - 负数保留负号（-350 → "-350.00"）

    ### 6. 备注
    提取"备注"、"说明"、"Notes"列的内容，无内容则为空字符串 ""

    ## 处理要点

    - 表格可能是 HTML `<table>` 或 Markdown `|` 格式
    - 同一文档可能有多个费用项，每项生成一个对象
    - OCR 错误的文本尽量理解语义
    - 如果整个文档都找不到某个字段，该字段在所有对象中都用 "" 填充

    ## 示例

    输入 Markdown：
    ```
    # 汕头市协运船务有限公司
    # 收款对账通知单
    工作单号: SEAE25090135
    费用明细：
    <table>
    <tr><td>费用名称</td><td>RMB</td><td>USD</td></tr>
    <tr><td>1.订舱费</td><td>350.00</td><td></td></tr>
    <tr><td>2.海运费</td><td></td><td>3360.00</td></tr>
    <tr><td>3.拖车费</td><td>1600.00</td><td></td></tr>
    </table>
    ```

    你必须输出（不要包含这段说明文字，只输出下面的 JSON）：
    {
        "费用明细": [
            {
                "外销合同": "SEAE25090135",
                "船代公司": "汕头市协运船务有限公司",
                "费用名称": "订舱费",
                "货币代码": "CNY",
                "金额": "350.00",
                "备注": ""
            },
            {
                "外销合同": "SEAE25090135",
                "船代公司": "汕头市协运船务有限公司",
                "费用名称": "海运费",
                "货币代码": "USD",
                "金额": "3360.00",
                "备注": ""
            },
            {
                "外销合同": "SEAE25090135",
                "船代公司": "汕头市协运船务有限公司",
                "费用名称": "拖车费",
                "货币代码": "CNY",
                "金额": "1600.00",
                "备注": ""
            }
        ]
    }

    ---

    现在开始处理以下文档，记住：只输出 JSON，不要有任何其他内容。

    ## 待处理文档：
    """ + content + """

    立即输出纯 JSON 格式结果："""

    return prompt

if __name__ == "__main__":
    # 测试代码
    test_file = "test.md"
    if os.path.exists(test_file):
        result = extract_info_from_md(test_file)
        print(result)
