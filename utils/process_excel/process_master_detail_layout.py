import os

import xlwings as xw

# 获取Excel文件的行数
def get_excel_row_count(input_file: str) -> int | None:
    """
    获取Excel文件中第一个工作表的行数
    
    参数：
        input_file (str): Excel文件路径
        
    返回：
        int: 工作表的行数
    """
    app = xw.App(visible=False)
    try:
        # 打开工作簿
        wb = app.books.open(input_file)
        # 获取第一个工作表
        sheet = wb.sheets[0]
        # 获取使用的范围
        used_range = sheet.used_range
        # 获取行数
        if used_range.value:
            row_count = used_range.rows.count
        else:
            row_count = 0
        wb.close()
        return row_count

    except Exception as e:
        print(f"获取Excel行数时出错: {e}")
        raise
    finally:
        app.quit()

# 按行切分Excel
def split_excel_by_rows(file_path, output_dir, rows_per_file=10):
    """
    将Excel表格按行切分，每`rows_per_file`行切分成一个新的Excel文件。
    保留原始格式（字体、颜色、边框、列宽、行高等）。

    参数：
        file_path (str): 输入Excel文件的路径。
        output_dir (str): 输出文件的目录。
        rows_per_file (int): 每个文件包含的行数，默认为10。

    返回：
        None
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    app = xw.App(visible=False)
    try:
        # 加载工作簿
        wb = app.books.open(file_path)
        sheet = wb.sheets[0]
        # 获取总行数和列数
        total_rows = sheet.used_range.rows.count
        total_cols = sheet.used_range.columns.count
        last_col_letter = xw.utils.col_name(total_cols)

        # 按行切分表格
        for start_row in range(1, total_rows + 1, rows_per_file):
            # 创建新的工作簿
            new_wb = app.books.add()
            new_sheet = new_wb.sheets[0]
            new_sheet.name = sheet.name

            # 复制当前分块的数据（包括格式）
            end_row = min(start_row + rows_per_file - 1, total_rows)
            data_range = sheet.range(f"A{start_row}:{last_col_letter}{end_row}")
            data_range.copy(new_sheet.range("A1"))

            # 删除数据区域的批注
            try:
                new_sheet.range(f"A1:{last_col_letter}{end_row - start_row + 1}").api.ClearComments()
            except:
                pass  # 如果没有批注，忽略错误

            # 复制列宽
            for col_idx in range(1, total_cols + 1):
                col_letter = xw.utils.col_name(col_idx)
                original_width = sheet.range(f"{col_letter}:{col_letter}").column_width
                new_sheet.range(f"{col_letter}:{col_letter}").column_width = original_width

            # 复制数据行的行高
            for row_idx in range(start_row, end_row + 1):
                original_height = sheet.range(f"{row_idx}:{row_idx}").row_height
                new_row_idx = row_idx - start_row + 1
                new_sheet.range(f"{new_row_idx}:{new_row_idx}").row_height = original_height

            # 保存新的工作簿
            output_file = os.path.join(
                output_dir,
                f"{sheet.name}_rows_{start_row}_to_{end_row}.xlsx",
            )
            new_wb.save(output_file)
            new_wb.close()
            print(f"已保存: {output_file}（已保留格式）")

        wb.close()
    except Exception as e:
        print(f"切分Excel文件时出错: {e}")
    finally:
        app.quit()

if __name__ == "__main__":
    print('Excel处理工具模块已加载')
    res = get_excel_row_count('调整列宽后.xlsx')
    split_row = int(res / 10)
    split_excel_by_rows('调整列宽后.xlsx', 'out_put', split_row)
