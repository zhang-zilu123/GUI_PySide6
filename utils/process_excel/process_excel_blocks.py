import os

import excel2img
from dashscope import MultiModalConversation

from config.config import EXCEL_TABLE_EXTRACTION_PROMPT
from dotenv import load_dotenv

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
    import xlwings as xw
    
    app = xw.App(visible=False)
    try:
        # 加载工作簿
        wb = app.books.open(file_path)

        for sheet in wb.sheets:
            # 获取使用范围
            used_range = sheet.used_range
            
            # 调整列宽
            for col_idx in range(1, used_range.columns.count + 1):
                col_letter = xw.utils.col_name(col_idx)
                col_range = sheet.range(f"{col_letter}:{col_letter}")
                max_length = 0
                
                for cell in col_range[:used_range.rows.count]:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                
                adjusted_width = (max_length + 2) * 1.2  # 调整宽度
                sheet.range(f"{col_letter}:{col_letter}").column_width = adjusted_width

            # xlwings 添加边框需要通过 API 对象
            # 为整个使用范围添加边框
            used_range.api.Borders.LineStyle = 1  # 1 表示实线边框

        # 保存格式化后的工作簿
        wb.save(file_path)
        wb.close()
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
    finally:
        app.quit()

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
    print('测试 Excel 格式化和数据提取')
