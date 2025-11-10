import os

import openpyxl
import excel2img
from dashscope import MultiModalConversation

from config.config import EXCEL_TABLE_EXTRACTION_PROMPT
from dotenv import load_dotenv
from openpyxl.styles import Border, Side

load_dotenv()

# 单个Excel文件进行列宽调整、添加边框，并转换为图片
def format_excel_and_convert_to_image(file_path, output_image_path):
    """
    给单个Excel文件调整列宽、添加全部框线，并转换为图片。

    参数：
        file_path (str): 输入Excel文件的路径。
        output_image_path (str): 输出图片的路径。

    返回：
        None
    """
    # 定义边框样式
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    try:
        # 加载工作簿
        workbook = openpyxl.load_workbook(file_path)

        for sheet in workbook.worksheets:
            # 调整列宽
            for col in sheet.columns:
                max_length = 0
                col_letter = col[0].column_letter  # 获取列字母
                for cell in col:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2  # 调整宽度
                sheet.column_dimensions[col_letter].width = adjusted_width

            # 添加边框
            for row in sheet.iter_rows():
                for cell in row:
                    cell.border = thin_border

        # 保存格式化后的工作簿
        workbook.save(file_path)
        print(f"已格式化: {file_path}")

        # 转换为图片
        excel2img.export_img(file_path, output_image_path)
        print(f"已转换为图片: {output_image_path}")

    except Exception as e:
        print(f"处理文件时出错: {file_path}, 错误: {e}")
        # 检查图片是否实际生成
        if os.path.exists(output_image_path):
            print(f"图片已生成，但导出过程出现警告: {output_image_path}")
            print(f"警告信息: {e}")
        else:
            raise e  # 如果图片未生成，则重新抛出异常

# 提取图片的数据输出markdown
def extract_excel_data_to_markdown(file_path):
    messages = [
        {
            "role": "user",
            "content": [{"image": file_path}, {"text": EXCEL_TABLE_EXTRACTION_PROMPT}]
        }
    ]

    response = MultiModalConversation.call(
        api_key=os.getenv("DASHSCOPE_API_KEY2"),
        model="qwen3-vl-plus",
        messages=messages,
    )
    return response.get("output").choices[0].get("message").get("content")[0].get("text")

if __name__ == "__main__":
    # 示例用法
    file_path = "./3、分块布局.xlsx"  # 替换为你的Excel文件路径
    output_image_path = "example.png"  # 替换为你的输出图片路径
    format_excel_and_convert_to_image(file_path, output_image_path)
    # res = extract_excel_data_to_markdown("./example.png")
    # print(res)
