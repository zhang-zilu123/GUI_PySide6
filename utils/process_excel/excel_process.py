import excel2img
import xlwings as xw

# 使用xlwings将.xls文件转换为.xlsx格式
def convert_xls_to_xlsx(input_file, output_file):
    app = xw.App(visible=False)
    wb = app.books.open(input_file)
    wb.save(output_file)
    wb.close()
    app.kill()

# 将Excel文件拆分为多个工作表
def split_excel_sheets(input_file, output_dir):
    """
    将一个Excel文件拆分为多个工作表，并将每个工作表保存为一个新的Excel文件。
    保留原始格式（字体、颜色、边框、列宽等）。

    参数：
        input_file (str): 输入Excel文件的路径。
        output_dir (str): 保存拆分工作表的目录。

    返回：
        None
    """
    import os

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    app = xw.App(visible=False)
    try:
        # 加载工作簿
        wb = app.books.open(input_file)

        # 遍历工作簿中的每个工作表
        for sheet in wb.sheets:
            sheet_name = sheet.name

            # 为当前工作表创建一个新的工作簿
            new_wb = app.books.add()
            new_sheet = new_wb.sheets[0]
            new_sheet.name = sheet_name

            # 复制整个工作表（包括格式）
            used_range = sheet.used_range
            if used_range.value:
                # 复制单元格内容和格式
                used_range.copy(new_sheet.range("A1"))
                
                # 复制列宽
                for col_idx in range(1, used_range.columns.count + 1):
                    col_letter = xw.utils.col_name(col_idx)
                    original_width = sheet.range(f"{col_letter}:{col_letter}").column_width
                    new_sheet.range(f"{col_letter}:{col_letter}").column_width = original_width
                
                # 复制行高
                for row_idx in range(1, used_range.rows.count + 1):
                    original_height = sheet.range(f"{row_idx}:{row_idx}").row_height
                    new_sheet.range(f"{row_idx}:{row_idx}").row_height = original_height

            # 保存新的工作簿
            output_file = os.path.join(output_dir, f"{sheet_name}.xlsx")
            try:
                new_wb.save(output_file)
                new_wb.close()
                print(f"已将工作表 '{sheet_name}' 保存到 '{output_file}'（已保留格式）")
            except Exception as e:
                print(f"保存工作表 '{sheet_name}' 时出错: {e}")

        wb.close()
    except Exception as e:
        print(f"加载工作簿时出错: {e}")
    finally:
        app.kill()

# 将Excel文件转换为图片
def convert_excel_to_images(file_paths, output_dir):
    """
    使用excel2img包将给定的Excel文件列表转换为图片。

    参数：
        file_paths (list): 包含Excel文件路径的列表。
        output_dir (str): 保存图片的目录。

    返回：
        None
    """
    import os

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍历文件路径列表中的所有Excel文件
    for input_file in file_paths:
        if input_file.endswith(".xlsx"):
            output_file = os.path.join(
                output_dir, f"{os.path.splitext(os.path.basename(input_file))[0]}.png"
            )

            try:
                # 将Excel转换为图片
                excel2img.export_img(input_file, output_file)
                print(f"已将 '{input_file}' 转换为 '{output_file}'")
            except Exception as e:
                print(f"转换 '{input_file}' 时出错: {e}")

if __name__ == "__main__":
    print('Excel处理工具模块已加载')
