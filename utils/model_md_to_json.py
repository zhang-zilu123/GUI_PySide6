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
    prompt = """
# 角色
你是一个顶级的数据结构化专家，专门从非结构化的 Markdown 文本中精准提取关键信息，并转换为结构化 JSON 格式。

# 任务
请从提供的一个费用单 Markdown 内容中，识别并提取以下 6 个字段：
- `外销合同`
- `船代公司`
- `费用名称`
- `货币代码`
- `金额`
- `备注`

将所有提取到的费用明细组织成一个结构化的 JSON 对象作为输出。

# 输出结构要求
1. 输出必须是一个 **合法的 JSON 对象**，顶层为一个键，其值是一个数组。
2. 顶层键名为 `"费用明细"`，其值为包含多个费用条目的数组。
3. 每一条费用信息为数组中的一个对象，必须包含上述 6 个字段。
4. 如果某个字段在原文中缺失，该字段仍需保留，值设为空字符串 `""`。
5. 所有字段值（包括金额）均以 **字符串形式** 返回，避免数值格式歧义。
6. 输出中 **不得包含任何额外说明、注释或 Markdown 代码块标记**（如 ```json）。


# 提取规则与逻辑说明
1. **外销合同**：
- 优先查找“合同号”、“委托编号”、“业务编号”、“外销合同”、“账单号”等关键词。
- 若存在多个候选，优先选择与 “委托编号” 或 “合同号” 对应的内容。
- 示例匹配模式：`合同号：(.+?)`、`委托编号：(.+?)`。

2. **船代公司**：
- **标签识别**（最高优先级）：
  - 寻找明确标签：`物流有限公司`、`船代公司：`、`船公司：`、`承运人：`、`代理公司：`、`船务代理：`、`服务商：`等；
  - 标签后的任何公司名称（包括简称如"MC"、"COSCO"等）都视为船代公司；
- **名称特征**（次优先级）：
  - 当无明确标签时，选择包含海运服务关键词的公司：`物流`、`海运`、`船务`、`港口`、`航运`、`船代`、`代理`、`供应链`、`货运`；
 - **位置识别**（备选方案）：
  - 账户信息区域中的公司（通常在银行账户信息附近）；
  - 费用明细表表头或表格上方的公司；
  - 费用单开具方或服务提供方位置的公司；
- **排除规则**：
  - 明确标注为`委托方`、`货主`、`收货人`、`发货人`的公司；
  - 纯贸易性质：仅包含`贸易`、`商贸`、`进出口`而无任何物流服务词汇的公司；
  - 非相关行业：包含`科技`、`制造`、`咨询`、`电子`、`机械`等与海运无关词汇的公司；

3. **费用名称**：
- 从费用表格中提取每一行的费用项目名称。
- 去除行首的编号（如 `1.`、`10.`），但保留中文或英文名称及括号内容。
- 示例：`场站费 (￥)` → `场站费`；`VGM 411漏收` → `VGM 411漏收`。

4. **货币代码**：
- 根据金额列的货币符号或“币别”列确定：
    - `￥` 或 `RMB` → `"CNY"`
    - `$` 或 `USD` → `"USD"`
    - `HKD` → `"HKD"`
    - `EUR` → `"EUR"`
    - `JPY` → `"JPY"`
- 若表格中有多币种列（如 RMB/USD），优先根据该行金额所在列判断。
- 若无明确币种，参考“总金额”或“人民币金额”等汇总信息推断。

5. **金额**：
- 提取每条费用对应的“合计”金额（非单价）。
- 清洗格式：去除货币符号、千分位逗号、空格等，仅保留数字和小数点。
- 转换为浮点数，保留两位小数(如 800.00 → 800.00、6,810.00 → 6810.00)。
- 若金额为空或为“-”，返回 `"0.00"`(浮点数)。


6. **备注**：
- 提取“说明”、“备注”、“Notes”等列的内容。
- 若无对应列，则根据行内额外文本（如“VGM 411漏收”）判断是否可作为备注。
- 否则留空 `""`。

# 特殊情况处理
- 若存在多行费用，每行生成一个独立对象。
- 表格可能以 HTML `<table>` 或 Markdown `|` 形式呈现，需兼容解析。
- 忽略“合计”、“总计”等汇总行。
- 若同一文本中出现多个币种，确保每条记录的货币代码与金额匹配。

# 示例1
输入示例（Markdown 片段）：
{{
# 费 用 单
<table><tr><td>项目</td><td colspan="2">单价</td><td>数量</td><td colspan="2">合计</td></tr><tr><td></td><td>RMB</td><td>USD</td><td></td><td>RMB</td><td>USD</td></tr><tr><td>1.海运费 ($)</td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>2.场站费 (￥)</td><td>400</td><td></td><td>2</td><td>￥800</td><td></td></tr><tr><td>3.港杂费 (￥)</td><td>373</td><td></td><td>2</td><td>￥746</td><td></td></tr><tr><td>4.单证费 (￥)</td><td>430</td><td></td><td>1</td><td>￥430</td><td></td></tr><tr><td>5. THC (￥)</td><td>990</td><td></td><td>2</td><td>￥1,980</td><td></td></tr><tr><td>6.舱单费 (￥)</td><td>150</td><td></td><td>1</td><td>￥150</td><td></td></tr><tr><td>7.QTS (￥)</td><td>500</td><td></td><td>2</td><td>￥1,000</td><td></td></tr><tr><td>8.AFR (￥)</td><td>225</td><td></td><td>1</td><td>￥225</td><td></td></tr><tr><td>10.代理费 (￥)</td><td>200</td><td></td><td>1</td><td>￥200</td><td></td></tr><tr><td>11.VGM (￥)</td><td>100</td><td></td><td>2</td><td>￥200</td><td></td></tr><tr><td>VGM 411漏收</td><td>100</td><td></td><td>1</td><td>￥100</td><td></td></tr><tr><td>合计</td><td colspan="2"></td><td></td><td>￥5,831.00</td><td>$0.0</td></tr></table>
如无回传视为默认  
<table><tr><td>帐户：</td><td></td></tr><tr><td>公司名称：</td><td>青岛林沃供应链管理有限公司</td></tr><tr><td>人民币开户行：</td><td>中国工商银行股份有限公司青岛奥帆支行</td></tr><tr><td>人民币账户：</td><td>3803021109200228547</td></tr><tr><td>美元开户行：</td><td>中国工商银行股份有限公司青岛奥帆支行</td></tr><tr><td>美元账户：</td><td>3803021119200216246</td></tr></table>
}}

输出示例（JSON）(仅显示前三个)：

```json
{
[
{
    "外销合同": "DJSCTAO250000746",
    "船代公司": "青岛林沃供应链管理有限公司",
    "费用名称": "海运费",
    "货币代码": "CNY",
    "金额": "0.00",
    "备注": ""
},
{
    "外销合同": "DJSCTAO250000746",
    "船代公司": "青岛林沃供应链管理有限公司",
    "费用名称": "场站费",
    "货币代码": "CNY",
    "金额": "800.00",
    "备注": ""
},
{
    "外销合同": "DJSCTAO250000746",
    "船代公司": "青岛林沃供应链管理有限公司",
    "费用名称": "港杂费",
    "货币代码": "CNY",
    "金额": "746.00",
    "备注": ""
}
]
}
```

# 结果格式要求:
* 返回一个顶层 JSON 对象，包含你提取到的全部信息。
# 开始处理
## 文本内容:
""" + content

    return prompt


if __name__ == "__main__":
    # 测试代码
    test_file = "test.md"
    if os.path.exists(test_file):
        result = extract_info_from_md(test_file)
        print(result)
