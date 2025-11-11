import os
import dashscope
import xlwings as xw
from dotenv import load_dotenv

load_dotenv()

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

# 使用 xlwings 读取 Excel 文件的前 20 行数据
def read_excel_first_20_rows(file_path):
    """
    使用 xlwings 读取 Excel 文件的前 20 行数据。
    """
    data = []
    app = xw.App(visible=False)
    try:
        wb = app.books.open(file_path)
        sheet = wb.sheets[0]
        # 获取实际使用的区域
        used_range = sheet.used_range
        total_rows = used_range.rows.count
        total_cols = used_range.columns.count
        # 只取前 20 行
        read_rows = min(20, total_rows)
        # 构造正确的范围字符串
        last_col_letter = xw.utils.col_name(total_cols)
        cell_range = f"A1:{last_col_letter}{read_rows}"
        # 一次性读取数据（比逐行快很多）
        data = sheet.range(cell_range).value
        wb.close()
    except Exception as e:
        print(f"读取 Excel 文件时出错: {e}")
    finally:
        app.quit()

    return data

# 按行切分Excel
def split_excel_by_rows_with_header(
        file_path, output_dir, header_index, rows_per_file=10
):
    """
    将Excel表格按行切分，每10行切分成一个新的Excel文件，且保留从第1行到表头索引行的所有数据。
    保留原始格式（字体、颜色、边框、列宽、行高等）。

    参数：
        file_path (str): 输入Excel文件的路径。
        output_dir (str): 输出文件的目录。
        header_index (int): 表头索引行的行号。
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
        for start_row in range(header_index + 1, total_rows + 1, rows_per_file):
            # 创建新的工作簿
            new_wb = app.books.add()
            new_sheet = new_wb.sheets[0]
            new_sheet.name = sheet.name

            # 复制从第1行到表头索引行的数据（包括格式）
            header_range = sheet.range(f"A1:{last_col_letter}{header_index}")
            header_range.copy(new_sheet.range("A1"))

            # 删除表头区域的批注
            try:
                new_sheet.range(f"A1:{last_col_letter}{header_index}").api.ClearComments()
            except:
                pass  # 如果没有批注，忽略错误

            # 复制当前分块的数据（包括格式）
            end_row = min(start_row + rows_per_file - 1, total_rows)
            data_range = sheet.range(f"A{start_row}:{last_col_letter}{end_row}")
            data_range.copy(new_sheet.range(f"A{header_index + 1}"))

            # 删除数据区域的批注
            try:
                new_sheet.range(
                    f"A{header_index + 1}:{last_col_letter}{header_index + (end_row - start_row + 1)}").api.ClearComments()
            except:
                pass  # 如果没有批注，忽略错误

            # 复制列宽
            for col_idx in range(1, total_cols + 1):
                col_letter = xw.utils.col_name(col_idx)
                original_width = sheet.range(f"{col_letter}:{col_letter}").column_width
                new_sheet.range(f"{col_letter}:{col_letter}").column_width = original_width

            # 复制表头行的行高
            for row_idx in range(1, header_index + 1):
                original_height = sheet.range(f"{row_idx}:{row_idx}").row_height
                new_sheet.range(f"{row_idx}:{row_idx}").row_height = original_height

            # 复制数据行的行高
            for row_idx in range(start_row, end_row + 1):
                original_height = sheet.range(f"{row_idx}:{row_idx}").row_height
                new_row_idx = row_idx - start_row + header_index + 1
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

# 格式化目录下所有Excel文件
def format_excel_files_in_directory(directory):
    """
    给目录下的所有Excel文件添加全部框线，并调整列宽以防止数据被遮挡。

    参数：
        directory (str): 包含Excel文件的目录路径。

    返回：
        None
    """
    import os

    # 遍历目录中的所有Excel文件
    file_paths = []
    app = xw.App(visible=False)
    try:
        for file_name in os.listdir(directory):
            if file_name.endswith(".xlsx"):
                file_path = os.path.join(directory, file_name)

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

                    # 保存修改
                    wb.save(file_path)
                    wb.close()
                    file_paths.append(file_path)
                    print(f"已格式化: {file_path}")
                except Exception as e:
                    print(f"格式化文件时出错: {file_path}, 错误: {e}")
    finally:
        app.quit()

    return file_paths

if __name__ == "__main__":
    print('测试 Excel 平铺布局处理工具模块')
    rows = read_excel_first_20_rows('./1、扁平布局.xls')
    print(rows)
