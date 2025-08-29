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
                你是一个顶级的数据结构化专家，专门从非结构化文本（特别是 Markdown）中精准提取关键信息，并将其组织成标准 JSON。

                # 任务:
                分析下面提供的多个 Markdown 文件内容。请仔细阅读并理解其结构与语义，提取所有有效信息，并组织为清晰、结构化的 JSON 对象。

                # 注意（总体要求）:
                * 你的输出**必须且仅限**为一个标准、可解析的 JSON；不要包含任何额外解释、Markdown 代码块标记或前后缀。
                * 严格保持原始信息的语义完整性，不增、不删、不臆测。
                * 当一行中出现多个字段时，必须识别为多个独立字段；严禁将同一值错误分配给多个键。
                * 确保每个 key 仅对应其真正关联的 value，且每个 value 仅归属其正确的 key，避免重复赋值或跨字段映射。
                * 充分利用冒号、空格、制表符、对齐、换行、列表符号、表格边界等分隔与布局特征来判断字段是否共存于同一行，并进行精确拆分与解析。
                * 若某行包含多个字段定义，应根据命名模式、对齐关系、值的唯一性与上下文含义来判定归属，防止误解析为共享同一值。
                * 对于多个文件，应将相同类型的信息进行归类整理，不同文件的数据可以放在数组中或以文件名作为键进行分组。

                # 语言与翻译规则（英文转中文）:
                * 在抽取前，先对 Markdown 文本中的**英文自然语言内容**进行准确的**简体中文**翻译，再执行字段识别与结构化。
                * 输出 JSON 中的**所有键（key）与值（value）一律使用简体中文**。
                * 下列内容**不翻译并保持原样**：专有名词（品牌/产品/机构/人名/地名等）、型号/机型、版本号、代号、ID/UUID、变量名、代码片段、命令、环境名、文件名/扩展名、路径、URL、邮箱、IP/端口、哈希、序列号/单号、时间戳、十六进制/二进制字面量。
                * 数字与货币金额保持原数值与格式；**计量单位名称可译**为中文（如 "kg"→"千克"、"cm"→"厘米"），但数值与小数点/千分位格式保持不变。
                * 中英混排时，只翻译其中的英文自然语言部分，确保句意不变。

                # 解析与结构化细则:
                * 标题/小节：识别层级结构；可在 JSON 中以嵌套对象或条目分组体现，但不得改变原有层级语义。
                * 列表/要点：保持顺序输出为数组；若列表项为键值对，需拆分为对象字段。
                * 表格（Markdown 表格或视觉对齐表格）：逐行逐列解析；首行/首列常为表头，应作为字段名；行数据输出为对象数组。
                * 键值对：优先识别中文/英文常见分隔符（如 "："、":"、"—"、"=" 等）；当存在多个键值对位于同一行时，逐对拆分。
                * 多字段同一行：根据分隔符、对齐、命名模式（如"编号/日期/数量/金额"等）分别产出独立字段；严禁将一个值复用到多个字段。
                * 重复字段名：若同一上层语义下出现同名字段且值不同，使用数组合并并保持顺序；若确系重复且值一致，可去重保留一个。
                * 缺失值：如仅出现字段名而无值，置为空字符串 ""。
                * 不确定字段名：在充分判断后仍无法合理命名时，使用 "未命名字段\_1"、"未命名字段\_2" … 等占位，但应尽量依据上下文给出贴切中文名称。
                * 时间/日期/区间：原样保留其表示方式；如需拆分（开始/结束），仅在文本中明确存在时才拆分。
                * 金额/币种：保留数值与币种标记；若币种以英文出现（如 "USD"），可在中文后括注（USD）或将币种名译为中文并保留原缩写（例如："美元（USD）"）。
                * 身份标识/编号：原样保留（不翻译），确保与对应字段严格对应。

                # 结果格式要求:
                * 返回一个顶层 JSON 对象，包含你提取到的全部信息。
                * 键名使用尽可能贴切的**中文字段名**；值使用翻译后的中文文本或原样保留的不可翻译内容。
                * 禁止输出与原文无关的字段；禁止生成示例/占位数据。
                * 严格遵守上述"多字段同一行""唯一归属""不重复赋值"等规则。

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
