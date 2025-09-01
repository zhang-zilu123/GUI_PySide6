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
                # 角色:
                你是一个顶级的数据结构化专家，专门从非结构化的 Markdown 文本中精准提取关键信息，并转换为结构化 JSON 格式。

                # 任务:
                给你一个费用单的 Markdown 文件内容，请你从中识别并提取以下 6 个字段：
                * 外销合同
                * 船代公司
                * 费用名称
                * 货币代码
                * 金额
                * 备注
                要求将所有提取结果组织成一个 JSON 对象。

                # 注意（总体要求）:
                1. JSON 必须是一个顶层对，其值是一个列表。
                2. 每一条费用信息为数组中的一个对象，包含上述 6 个字段。
                3. 如果某个字段缺失，仍然需要返回该字段，值设为空字符串 `""`。
                4. 输出必须是严格合法的 JSON，不能包含额外说明或注释。
                5. 所有数值（如金额）也以字符串形式返回，避免格式歧义。
                
                # 结果(示例)
                输入示例（Markdown 片段）：
                ```
                外销合同  船代公司  费用名称  货币代码  金额  备注
                L25RU03059  宁波盛威国际物流有限公司  预进费 CNY 596.00  
                L25RU03059  宁波盛威国际物流有限公司  陆运费（门到门）  CNY 3200.00 横街
                ```
                
                输出示例（JSON）：
                
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
                      "金额": "3200.00",
                      "备注": "横街"
                    }
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
