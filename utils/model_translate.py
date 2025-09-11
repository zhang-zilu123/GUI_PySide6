from openai import OpenAI
from random import choice
import os
import time
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from data.temp_data import get_data

os.environ["DASHSCOPE_API_KEY1"] = "sk-ca1bef1139754026b86788af0dbbbbd4"
os.environ["DASHSCOPE_API_KEY2"] = "sk-381d3df1c3ee4623bb9a1b9c767f7b5e"
os.environ["DASHSCOPE_API_KEY3"] = "sk-22d825174e1143d8ba6822880addf9ea"

dash_keys = [
    os.getenv("DASHSCOPE_API_KEY1"),
    os.getenv("DASHSCOPE_API_KEY2"),
    os.getenv("DASHSCOPE_API_KEY3"),
]


def translate_json(content) -> str:
    """从json文件中翻译船代公司"""

    client = OpenAI(
        api_key=choice(dash_keys),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    response = client.chat.completions.create(
        # model="qwen-max",
        # model="qwen-plus",
        model="qwen-flash",

        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant designed to output JSON.'},
            {'role': 'user', 'content': f"""
# 背景
- 文本来源于**外贸公司的货代发票或费用单**，其中包含合同号、公司信息及费用明细。
- 这些公司主要包括：
  1. 国际船运公司（如马士基、地中海、达飞、赫伯罗特等）
  2. 货运代理公司（如中外运、嘉里物流等）
  3. 物流服务提供商（如敦豪、联邦等）
  4. 港口和码头运营商
  5. 供应链管理公司
- 公司名称通常包含以下要素：
  1. 公司类型标识（如：货运、物流、船务、供应链等）
  2. 业务范围（如：国际、全球、远东等）
  3. 企业性质（如：有限公司、股份公司等）
  4. 分支机构说明（如：宁波分公司、青岛办事处等）

# 角色
你是一名专业的国际物流翻译专家，具备：
1. 深入理解外贸物流行业术语和公司命名规范
2. 熟悉中国主要港口城市的物流公司分布
3. 了解国际知名物流企业的官方中文译名
4. 掌握物流行业相关法律法规和标准译名

# 任务
从提供的 JSON 数据中：
- 仅翻译以下字段：
  - `船代公司`：将英文的公司名称准确翻译为规范的中文名称
             
- 以下字段保持原文，不做翻译：
  - `外销合同`
  - `费用名称`
  - `备注`
  - `货币代码` 
  - `金额` 

# 翻译规则
1. 公司名称翻译规范：
   - 使用公司在中国的官方注册中文名称（如有）
   - 遵循"地区+公司名+业务类型+公司性质+分支机构"的标准格式
   - 正确使用"有限公司"、"股份有限公司"等企业类型表述
   - 准确翻译分支机构类型（分公司、办事处、代表处等）

2. 特殊情况处理：
   - 缩写处理：将 CO LTD 转换为"有限公司"，Inc. 转换为"股份有限公司"等
   - 地名翻译：使用官方认可的地名译名（如：NINGBO → 宁波）
   - 合资公司：保留外方公司名称的通用翻译（如：Maersk → 马士基）
   - 品牌名称：使用市场通用的中文名称（如：DHL → 敦豪）

3. 格式要求：
   - 保留 JSON 结构与字段顺序
   - 确保输出为合法 JSON
   - 不添加任何注释或额外标记

4. 质量标准：
   - 符合中国工商登记的公司名称规范
   - 使用专业、规范的物流行业用语
   - 保持命名的一致性和准确性
   - 避免生硬的直译和不专业的表达

# 输出结构要求
1. 输出为一个 JSON 对象
2. JSON结构保持不变
3. 数组内的每个对象必须包含以下字段：
   - `外销合同`（保持原文）
   - `船代公司`（翻译成规范中文名称）
   - `费用名称`（保持原文）
   - `货币代码`（保持原文）
   - `金额`（保持原文）
   - `备注`（保持原文）

# 示例1
输入示例（json 片段）：
```json
{[{
"外销合同": "742N004924NB0",
"船代公司": "Century Distribution Systems (Shenzhen) Ltd-Ningbo Branch",
"费用名称": "柜子费",
"货币代码": "CNY",
"金额": "160.00",
"备注": ""
},
{
"外销合同": "742N004924NB0",
"船代公司": "Century Distribution Systems (Shenzhen) Ltd-Ningbo Branch",
"费用名称": "CUSTOMS CLEARANCE/DECLARATION (EXPORT)",
"货币代码": "CNY",
"金额": "130.00",
"备注": ""
}]}
```

输出示例（JSON）：

```json
{ [{
                "外销合同": "742N004924NB0",
                "船代公司": "世纪冠航国际货运代理（深圳）有限公司宁波分公司",
                "费用名称": "柜子费",
                "货币代码": "CNY",
                "金额": "160.00",
                "备注": ""
            },
            {
                "外销合同": "742N004924NB0",
                "船代公司": "世纪冠航国际货运代理（深圳）有限公司宁波分公司",
                "费用名称": "CUSTOMS CLEARANCE/DECLARATION (EXPORT)",
                "货币代码": "CNY",
                "金额": "130.00",
                "备注": ""
            }
        ] }
```

# 开始处理
## 文本内容:
{content}

"""
            },
        ],
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    #     content = """
    #     {
    # "外销合同": "DJSCTAO250000746",
    # "船代公司": "GOURMET HOME PRODUCTS LLC",
    # "费用名称": "海运费",
    # "货币代码": "CNY",
    # "金额": "0.00",
    # "备注": ""
    # }
    #
    #
    #     """
    start_time = time.time()
    start_datetime = datetime.now()
    content = get_data()
    print(translate_json(content))
    end_time = time.time()
    end_datetime = datetime.now()
    print(f"总耗时: {end_time - start_time} 秒")
