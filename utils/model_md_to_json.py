from openai import OpenAI
from random import choice
import os
import json

os.environ["DASHSCOPE_API_KEY1"] = "sk-ca1bef1139754026b86788af0dbbbbd4"
os.environ["DASHSCOPE_API_KEY2"] = "sk-381d3df1c3ee4623bb9a1b9c767f7b5e"
os.environ["DASHSCOPE_API_KEY3"] = "sk-22d825174e1143d8ba6822880addf9ea"

dash_keys = [
    os.getenv("DASHSCOPE_API_KEY1"),
    os.getenv("DASHSCOPE_API_KEY2"),
    os.getenv("DASHSCOPE_API_KEY3"),
]


def extract_info_from_md(md_file_paths: list) -> dict:
    """从多个 markdown 文件中提取信息"""
    all_content = ""

    # 读取所有 md 文件内容
    for md_file_path in md_file_paths:
        if not os.path.exists(md_file_path):
            print(f"错误: 文件 {md_file_path} 不存在。")
            continue

        try:
            with open(md_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # 添加文件标识和内容
                filename = os.path.basename(md_file_path).replace('.md', '')
                all_content += f"\n\n## 文件: {filename}\n{content}\n"
        except Exception as e:
            print(f"读取文件 {md_file_path} 时出错: {e}")
            continue

    if not all_content.strip():
        print("没有成功读取到任何文件内容")
        return {}

    client = OpenAI(
        api_key=choice(dash_keys),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    response = client.chat.completions.create(
        model="qwen-max",

        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant designed to output JSON.'},
            {'role': 'user', 'content': f"""
                # 角色
                你是一个顶级的数据结构化专家，专门从非结构化的 Markdown 文本中精准提取关键信息，并转换为结构化 JSON 格式。

                # 任务
                请从提供的费用单 Markdown 内容中，识别并提取以下 6 个字段：
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
                - 若多个候选存在，优先选择与“委托编号”或“合同号”关联的值。
                - 示例匹配模式：`合同号：(.+?)`、`委托编号：(.+?)`。

                2. **船代公司**：
                - 查找文本开头或公司信息区块中的公司名称。
                - 优先匹配第一行非空文本且包含“公司”字样的条目，或“船代公司”、“公司名称”等字段。
                - 示例：`宁波盛威国际物流有限公司`、`青岛林沃供应链管理有限公司`。

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
                - 统一格式为保留两位小数的字符串（如 `"800.00"`）。
                - 若金额为空或为“-”，返回 `"0.00"`。

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
                      "备注": ""}
                      
                  ]
                }
                ```


                # 示例2
                输入示例（Markdown 片段）：
                {{
                宁波盛威国际物流有限公司
                业务编号：SFLE25080258
                委托编号：L25RU03059
                委托方：宁波荣御国际贸易有限公司
                船名/航次：DELAWARE EXPRESS V.533E
                主单号：256867624
                合同号：256867624
                起运港：NINGBO
                目的港：LOS ANGELES, CA
                箱型箱量：4X40'HQ
                ETD：2025-08-21
                总金额：
                人民币金额：6076 CNY
                港元金额：0 HKD
                美元金额：0 USD
                欧元金额：0 EUR
                日币金额：0 JPY
                联系信息：
                联系人：陈飞盈
                电话：28913640
                传真：（未提供）
                日期：2025-08-23
                | 费用项目   | 单价 | 数量 | 金额 | 币别 | 汇率 | 说明   |
                |:-----------|-----:|-----:|-----:|:----|-----:|:-------|
                | 预进费     |  149 |    4 |  596 | CNY |    1 | 说明   |
                | 陆运费（门到门） |  800 |    4 | 3200 | CNY |    1 | 横街   |
                | 报关费     |  100 |    1 |  100 | CNY |    1 | 横街   |
                | 提箱费     |  200 |    4 |  800 | CNY |    1 | 梅山   |
                | 进港费     |  300 |    4 | 1200 | CNY |    1 | 梅山   |
                | 条形码     |   45 |    4 |  180 | CNY |    1 | 梅山   |
                | 港杂费     |   50 |    4 |  200 | CNY |    1 | 横街   |   

                }}
                
                输出示例（JSON）(仅显示前三个)：
                
                ```json
                {
                  [
                    {
                      "外销合同": "L25RU03059",
                      "船代公司": "宁波盛威国际物流有限公司",
                      "费用名称": "预进费",
                      "货币代码": "CNY",
                      "金额": "596.00",
                      "备注": ""
                    },
                    {
                      "外销合同": "L25RU03059",
                      "船代公司": "宁波盛威国际物流有限公司",
                      "费用名称": "陆运费（门到门）",
                      "货币代码": "CNY",
                      "金额": "100.00",
                      "备注": ""
                    },
                    {
                      "外销合同": "L25RU03059",
                      "船代公司": "宁波盛威国际物流有限公司",
                      "费用名称": "报关费",
                      "货币代码": "CNY",
                      "金额": "800.00",
                      "备注": ""}
                      
                  ]
                }
                ```

                # 结果格式要求:
                * 返回一个顶层 JSON 对象，包含你提取到的全部信息。
                # 开始处理
                ## 文本内容:
                {all_content}
                """
             },
        ],

        response_format={"type": "json_object"}
    )

    result = response.choices[0].message.content
    return result


if __name__ == "__main__":
    md_file_paths = [
        r"output1\G25RU03088费用明细\auto\G25RU03088费用明细.md",
        
    ]
    result = extract_info_from_md(md_file_paths)
    print(result)
