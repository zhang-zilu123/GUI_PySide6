import os
import json
import uuid
import xlwings as xw
from typing import List, Tuple, Dict, Any
from PySide6.QtCore import Signal, SignalInstance

from utils.process_excel.excel_process import (
    convert_xls_to_xlsx,
    split_excel_sheets,
    convert_excel_to_images,
    auto_adjust_excel_column_width,
)
from utils.process_excel.excel_llm import detect_excel_layout, determine_header_index, extract_excel_data_to_markdown, \
    correct_excel_table
from utils.process_excel.process_flat_layout import (
    read_excel_first_20_rows,
    split_excel_by_rows_with_header,
    format_excel_files_in_directory,
)
from utils.process_excel.process_excel_blocks import (
    format_excel_and_convert_to_image,
)
from utils.process_excel.process_master_detail_layout import (
    get_excel_row_count,
    split_excel_by_rows,
)
from utils.model_md_to_json import extract_info_from_md
from utils.logger import get_file_conversion_logger, get_error_logger

# 使用统一的日志系统
logger = get_file_conversion_logger()
error_logger = get_error_logger()

class ExcelProcessHandler:
    """Excel文件处理器"""

    def __init__(self, output_dir: str, status_signal: SignalInstance = None,
                 original_file_mapping: Dict[str, str] = None):
        """
        初始化Excel处理器

        参数：
            output_dir: 输出目录
            status_signal: 状态更新信号（可选）
            original_file_mapping: 临时文件路径到原始文件路径的映射
        """
        self.output_dir = output_dir
        self.status_signal = status_signal
        self.original_file_mapping = original_file_mapping or {}

    def _emit_status(self, message: str):
        """发送状态更新信号"""
        if self.status_signal:
            self.status_signal.emit(message)

    def process_excel_files_batch(self, excel_files: List[Tuple[str, str]]) -> dict:
        """
        批量处理多个Excel文件

        参数：
            excel_files: [(file_path, base_name), ...] Excel文件路径和基础名称的列表

        返回：
            包含所有处理结果的字典
        """
        result = {
            "files": [],
            "excel_data": [],
            "file_mapping": {},  # 结果文件名 -> 原始文件路径
        }

        # 第一阶段：准备所有Excel文件（转换xls、拆分sheet、生成图片）
        all_sheets_info = (
            []
        )  # [(sheet_path, sheet_name, image_path, original_file, safe_name), ...]

        self._emit_status(f"正在准备 {len(excel_files)} 个Excel文件...")

        for file_path, base_name in excel_files:
            # 处理中文文件名
            safe_base_name = self._generate_safe_filename(base_name)
            print(f"文件名处理: {base_name} -> {safe_base_name}")

            # 创建工作目录
            excel_work_dir = os.path.join(
                self.output_dir, f"excel_work_{safe_base_name}"
            )
            os.makedirs(excel_work_dir, exist_ok=True)

            # 转换xls为xlsx
            xlsx_file = file_path
            if file_path.lower().endswith(".xls"):
                self._emit_status(f"正在转换 .xls 为 .xlsx: {base_name}")
                xlsx_file = os.path.join(excel_work_dir, f"{safe_base_name}.xlsx")
                convert_xls_to_xlsx(file_path, xlsx_file)
                print(f"已转换 .xls 为 .xlsx: {xlsx_file}")

            # 拆分sheet
            self._emit_status(f"正在拆分工作表: {base_name}")
            split_dir = os.path.join(excel_work_dir, "split_sheets")
            os.makedirs(split_dir, exist_ok=True)
            split_excel_sheets(xlsx_file, split_dir)

            # 获取有效的sheet文件
            all_split_files = [
                os.path.join(split_dir, f)
                for f in os.listdir(split_dir)
                if f.endswith(".xlsx")
            ]

            split_files = []
            for file in all_split_files:
                if not self._is_excel_empty(file):
                    split_files.append(file)
                else:
                    print(f"跳过空的 Excel 文件: {os.path.basename(file)}")
                    try:
                        os.remove(file)
                    except:
                        pass

            print(f"'{base_name}' 拆分后有效文件数量: {len(split_files)}")

            if not split_files:
                print(f"警告: Excel 文件 '{base_name}' 的所有工作表都为空，跳过处理")
                continue

            # 转换为图片
            self._emit_status(f"正在转换为图片: {base_name}")
            image_dir = os.path.join(excel_work_dir, "images")
            os.makedirs(image_dir, exist_ok=True)
            convert_excel_to_images(split_files, image_dir)

            # 收集sheet信息
            for split_file in split_files:
                sheet_name = os.path.splitext(os.path.basename(split_file))[0]
                image_file = os.path.join(image_dir, f"{sheet_name}.png")

                if os.path.exists(image_file):
                    all_sheets_info.append(
                        {
                            "sheet_path": split_file,
                            "sheet_name": sheet_name,
                            "image_path": image_file,
                            "original_file": file_path,
                            "safe_name": safe_base_name,
                            "work_dir": excel_work_dir,
                            "base_name": base_name,
                        }
                    )
                else:
                    print(f"图片文件不存在，跳过: {image_file}")

        if not all_sheets_info:
            print("没有找到可用的sheet进行处理")
            return result

        # 第二阶段：批量布局检测（一次性检测所有图片）
        print(f"\n{'=' * 60}")
        print(f"收集到 {len(all_sheets_info)} 个sheet，开始批量布局检测...")
        print(f"{all_sheets_info}")
        print(f"{'=' * 60}\n")

        self._emit_status(f"正在批量检测布局类型（共{len(all_sheets_info)}个工作表）...")

        all_image_paths = [info["image_path"] for info in all_sheets_info]
        print(f"批量检测图片: {all_image_paths}")
        layout_results = detect_excel_layout(all_image_paths)
        print(f"批量布局检测结果: {layout_results}")

        # 解析布局结果
        try:
            if isinstance(layout_results, str):
                layout_dict = json.loads(layout_results)
            else:
                layout_dict = layout_results
        except Exception as e:
            print(f"解析布局检测结果失败: {e}, 使用默认布局")
            layout_dict = {}

        # 为每个sheet添加布局类型
        for idx, sheet_info in enumerate(all_sheets_info):
            layout_key = f"index_{idx + 1}"
            layout_num = layout_dict.get(layout_key, 0)
            try:
                layout_num = int(layout_num)
            except:
                print(f"无法解析布局类型 {layout_key}: {layout_num}，默认为类型0")
                layout_num = 0
            sheet_info["layout_type"] = layout_num

        # 第三阶段：按布局类型分组
        layout_groups = {}
        for sheet_info in all_sheets_info:
            layout_type = sheet_info["layout_type"]
            if layout_type not in layout_groups:
                layout_groups[layout_type] = []
            layout_groups[layout_type].append(sheet_info)

        print(f"\n布局分组结果:")
        for layout_type, sheets in sorted(layout_groups.items()):
            print(f"  布局{layout_type}: {len(sheets)}个sheet")

        # 第四阶段：按布局类型队列处理
        print(f"\n{'=' * 60}")
        print(f"开始按布局类型队列处理...")
        print(f"{'=' * 60}\n")

        # 处理顺序：1(扁平式) -> 3(分块式) -> 2(主表+子表) -> 0(其他)
        process_order = [1, 3, 0, 2]

        for layout_type in process_order:
            if layout_type not in layout_groups:
                continue

            sheets = layout_groups[layout_type]
            print(f"\n>>> 处理布局类型 {layout_type} ({len(sheets)} 个sheet)")

            for idx, sheet_info in enumerate(sheets):
                print(
                    f"  [{idx + 1}/{len(sheets)}] {sheet_info['base_name']} - {sheet_info['sheet_name']}"
                )

                # 处理单个sheet
                sheet_result = self._process_single_sheet(sheet_info, layout_type)

                if sheet_result:
                    result["files"].extend(sheet_result.get("files", []))
                    result["excel_data"].extend(sheet_result.get("data", []))

                    # 更新文件映射
                    for file in sheet_result.get("files", []):
                        file_name = os.path.splitext(os.path.basename(file))[0]
                        result["file_mapping"][file_name] = sheet_info["original_file"]

        print("处理完成", result)
        return result

    def _process_single_sheet(self, sheet_info: dict, layout_type: int) -> dict:
        """
        处理单个sheet

        参数：
            sheet_info: sheet信息字典
            layout_type: 布局类型

        返回：
            处理结果字典
        """
        result = {"files": [], "data": []}

        sheet_path = sheet_info["sheet_path"]
        sheet_name = sheet_info["sheet_name"]
        work_dir = sheet_info["work_dir"]
        original_file = sheet_info["original_file"]

        if layout_type == 1:
            # 扁平式布局
            self._emit_status(f"处理扁平式布局: {sheet_name}")
            image_files = self._process_flat_layout(sheet_path, sheet_name, work_dir)
            result["files"].extend(image_files)

            if image_files:
                self._emit_status(f"正在提取扁平式布局数据: {sheet_name}")
                flat_data = self._extract_flat_layout_data(image_files)
                # 使用原始文件路径
                display_file = self.original_file_mapping.get(original_file, original_file)
                for item in flat_data:
                    item["源文件"] = display_file
                result["data"].extend(flat_data)

        elif layout_type == 2:
            # 主表+子表布局
            self._emit_status(f"处理主表+子表布局: {sheet_name}")
            result_data = self._process_master_detail_layout(sheet_path, sheet_name, work_dir)

            if result_data:
                result["files"].extend(result_data["files"])
                self._emit_status(f"正在提取主表+子表布局数据: {sheet_name}")
                master_detail_data = self._extract_block_layout_data(
                    result_data["markdown"], original_file
                )
                result["data"].extend(master_detail_data)

        elif layout_type == 3:
            # 分块布局
            self._emit_status(f"处理分块布局: {sheet_name}")
            result_data = self._process_block_layout(sheet_path, sheet_name, work_dir)

            if result_data:
                result["files"].append(result_data["file"])
                self._emit_status(f"正在提取分块布局数据: {sheet_name}")
                block_data = self._extract_block_layout_data(
                    result_data["markdown"], original_file
                )
                result["data"].extend(block_data)

        else:
            self._emit_status(f"处理主表+子表布局: {sheet_name}")
            result_data = self._process_master_detail_layout(sheet_path, sheet_name, work_dir)

            if result_data:
                result["files"].extend(result_data["files"])
                self._emit_status(f"正在提取主表+子表布局数据: {sheet_name}")
                master_detail_data = self._extract_block_layout_data(
                    result_data["markdown"], original_file
                )
                result["data"].extend(master_detail_data)

        return result

    def _process_flat_layout(
            self, excel_file: str, sheet_name: str, work_dir: str
    ) -> list:
        """
        处理扁平式布局的 Excel

        返回：
            处理后的图片文件路径列表
        """
        # 读取前20行确定表头
        self._emit_status(f"正在分析表头: {sheet_name}")
        rows = read_excel_first_20_rows(excel_file)
        header_index = int(determine_header_index(rows))
        print(f"表头索引: {header_index} for {sheet_name}")

        # 按行切分
        self._emit_status(f"正在切分表格: {sheet_name}")
        split_output_dir = os.path.join(work_dir, f"flat_split_{sheet_name}")
        os.makedirs(split_output_dir, exist_ok=True)
        split_excel_by_rows_with_header(
            excel_file, split_output_dir, header_index + 1, rows_per_file=5
        )

        # 格式化所有切分后的文件
        self._emit_status(f"正在格式化表格: {sheet_name}")
        formatted_files = format_excel_files_in_directory(split_output_dir)

        # 转换为图片
        self._emit_status(f"正在转换为图片: {sheet_name}")
        image_output_dir = os.path.join(work_dir, f"flat_images_{sheet_name}")
        os.makedirs(image_output_dir, exist_ok=True)
        convert_excel_to_images(formatted_files, image_output_dir)

        # 返回所有图片文件路径
        image_files = [
            os.path.join(image_output_dir, f)
            for f in os.listdir(image_output_dir)
            if f.endswith(".png")
        ]
        print(f"生成图片数量: {len(image_files)} for {sheet_name}")

        return image_files

    def _process_block_layout(
            self,
            excel_file: str,
            sheet_name: str,
            work_dir: str,
    ) -> dict:
        """
        处理分块布局的 Excel

        返回：
            包含文件路径和 markdown 数据的字典
        """
        # 格式化并转换为图片
        self._emit_status(f"正在格式化和转换: {sheet_name}")
        image_output = os.path.join(work_dir, f"block_image_{sheet_name}.png")
        format_excel_and_convert_to_image(excel_file, image_output)

        # 使用大模型提取数据
        self._emit_status(f"正在提取数据: {sheet_name}")
        markdown_content = extract_excel_data_to_markdown([image_output])
        print(f"提取的 Markdown 内容长度: {len(markdown_content)} for {sheet_name}")

        return {
            "file": image_output,
            "markdown": markdown_content,
        }

    def _process_master_detail_layout(
            self,
            excel_file: str,
            sheet_name: str,
            work_dir: str,
    ) -> dict:
        """
        处理主表+子表布局的 Excel

        返回：
            包含文件路径列表和 markdown 数据的字典
        """
        # 1. 调整列宽
        self._emit_status(f"正在调整列宽: {sheet_name}")
        adjusted_file = os.path.join(work_dir, f"adjusted_{sheet_name}.xlsx")
        auto_adjust_excel_column_width(excel_file, adjusted_file)
        print(f"列宽调整完成: {adjusted_file}")

        # 2. 获取Excel行数
        self._emit_status(f"正在获取行数: {sheet_name}")
        row_count = get_excel_row_count(adjusted_file)
        print(f"Excel总行数: {row_count} for {sheet_name}")

        # 3. 计算每个文件的行数（按10份切分）
        if row_count <= 150:
            rows_per_file = min(row_count, 40)
        elif row_count <= 400:
            rows_per_file = min(70, max(40, int(row_count / 6)))
        else:
            rows_per_file = min(80, max(40, int(row_count / (row_count // 70))))
        print(f"每个文件行数: {rows_per_file}")

        # 4. 按行切分成多个Excel文件
        self._emit_status(f"正在切分表格: {sheet_name}")
        split_output_dir = os.path.join(work_dir, f"master_detail_split_{sheet_name}")
        os.makedirs(split_output_dir, exist_ok=True)
        split_excel_by_rows(adjusted_file, split_output_dir, rows_per_file)
        print(f"Excel切分完成: {split_output_dir}")

        # 5. 获取切分后的文件列表（按文件名排序）
        split_files = sorted([
            os.path.join(split_output_dir, f)
            for f in os.listdir(split_output_dir)
            if f.endswith(".xlsx")
        ])
        print(f"切分后文件数量: {len(split_files)}")

        # 6. 将所有Excel文件转换为图片
        self._emit_status(f"正在转换为图片: {sheet_name}")
        image_output_dir = os.path.join(work_dir, f"master_detail_images_{sheet_name}")
        os.makedirs(image_output_dir, exist_ok=True)
        convert_excel_to_images(split_files, image_output_dir)

        # 7. 获取所有图片文件（按文件名中的起始行号排序）
        import re

        def extract_start_row(filename):
            """从文件名中提取起始行号用于排序"""
            match = re.search(r'rows_(\d+)_to_\d+\.png$', filename)
            if match:
                return int(match.group(1))
            return 0

        image_files = sorted(
            [os.path.join(image_output_dir, f) for f in os.listdir(image_output_dir) if f.endswith(".png")],
            key=lambda x: extract_start_row(os.path.basename(x))
        )
        print(f'图片:{[os.path.basename(f) for f in image_files]}')
        print(f"生成图片数量: {len(image_files)}")

        # 8. 按顺序将所有图片输入到大模型提取数据
        self._emit_status(f"正在提取数据: {sheet_name}")
        markdown_content = extract_excel_data_to_markdown(image_files)
        print(f"提取的 Markdown 内容长度: {len(markdown_content)} for {sheet_name}")

        return {
            "files": image_files,
            "markdown": markdown_content,
        }

    def _extract_flat_layout_data(self, image_files: List[str]) -> List[Dict[str, Any]]:
        """
        从扁平式布局的图片中提取数据

        参数：
            image_files: 图片文件路径列表

        返回：
            提取的数据列表
        """
        from controllers.extract_data_controller import ExtractDataWorker

        # 创建一个临时的提取工作线程（但不启动线程，直接调用方法）
        worker = ExtractDataWorker(image_files)

        # 如果有状态信号，连接它
        if self.status_signal:
            worker.status_updated.connect(lambda msg: self._emit_status(msg))

        try:
            # 直接调用提取方法
            extracted_data = worker.extract_data_from_pdf(image_files)
            print(f"扁平式布局数据提取完成，共 {len(extracted_data)} 条记录")
            return extracted_data
        except Exception as e:
            error_msg = f"扁平式布局数据提取失败: {str(e)}"
            print(error_msg)
            error_logger.error(error_msg)
            return []

    def _extract_block_layout_data(
            self, markdown_content: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        从分块布局的 markdown 内容中提取结构化数据

        参数：
            markdown_content: Markdown 内容
            file_path: 源文件路径

        返回：
            提取的数据列表
        """
        try:
            # extract_info_from_md 返回的是 JSON 字符串，需要解析
            json_result = extract_info_from_md("", markdown_content)
            print(f"提取的 JSON 结果类型: {type(json_result)}")

            # 如果返回的是字符串，解析为 Python 对象
            if isinstance(json_result, str):
                parsed_data = json.loads(json_result)
            else:
                parsed_data = json_result

            # 提取费用明细列表
            display_data = []
            if isinstance(parsed_data, dict):
                # 如果是字典，尝试提取费用明细
                if "费用明细" in parsed_data:
                    display_data = parsed_data["费用明细"]
                else:
                    # 如果没有费用明细字段，尝试直接使用整个字典
                    display_data = [parsed_data]
            elif isinstance(parsed_data, list):
                display_data = parsed_data

            # 使用原始文件路径
            display_file = self.original_file_mapping.get(file_path, file_path)
            for item in display_data:
                item["源文件"] = display_file
            print(f"分块布局数据提取完成，共 {len(display_data)} 条记录")
            return display_data

        except Exception as e:
            error_msg = f"分块布局数据提取失败: {str(e)}"
            print(error_msg)
            error_logger.error(error_msg)
            return []

    def _generate_safe_filename(self, filename: str) -> str:
        """
        生成安全的文件名（移除或替换中文字符）

        参数：
            filename: 原始文件名

        返回：
            安全的文件名（仅包含ASCII字符）
        """
        # 检查是否包含中文或其他非ASCII字符
        has_non_ascii = not all(ord(char) < 128 for char in filename)

        if not has_non_ascii:
            # 如果文件名已经是纯ASCII，直接返回
            return filename

        # 生成唯一的文件名：使用时间戳和UUID
        import time

        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        unique_id = str(uuid.uuid4())[:8]  # 取UUID的前8位

        safe_name = f"excel_{timestamp}_{unique_id}"
        print(f"中文文件名转换: '{filename}' -> '{safe_name}'")
        logger.info(f"中文文件名转换: '{filename}' -> '{safe_name}'")

        return safe_name

    def _is_excel_empty(self, file_path: str) -> bool | None:
        """
        使用 xlwings 检查 Excel 文件是否为空（没有数据或只有空行）

        参数：
            file_path: Excel 文件路径

        返回：
            如果文件为空返回 True，否则返回 False
        """
        app = xw.App(visible=False)
        try:
            wb = app.books.open(file_path)
            sheet = wb.sheets[0]

            # 检查是否有任何非空单元格
            used_range = sheet.used_range
            if used_range.value:
                for row in used_range.value:
                    if any(cell is not None and str(cell).strip() for cell in row):
                        return False

            # 所有单元格都是空的
            return True

        except Exception as e:
            print(f"检查 Excel 文件是否为空时出错: {file_path}, 错误: {str(e)}")
            # 如果出错，假设文件不为空，继续处理
            return False

        finally:
            app.quit()
