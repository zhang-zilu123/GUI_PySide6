import os
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any
from PySide6.QtCore import QThread, Signal

from utils.file_to_pdf import excel_to_pdf, docx_to_pdf, rtf_to_pdf
from utils.logger import get_file_conversion_logger, get_error_logger
from utils.model_md_to_json import extract_info_from_md
from utils.process_excel.excel_process import (
    convert_xls_to_xlsx,
    split_excel_sheets,
    convert_excel_to_images,
)
from utils.process_excel.excel_layout_analyzer import detect_excel_layout
from utils.process_excel.process_flat_layout import (
    read_excel_first_20_rows,
    determine_header_index,
    split_excel_by_rows_with_header,
    format_excel_files_in_directory,
)
from utils.process_excel.process_excel_blocks import (
    format_excel_and_convert_to_image,
    extract_excel_data_to_markdown,
)

# 使用统一的日志系统（与 upload_controller 共享日志文件）
logger = get_file_conversion_logger()
error_logger = get_error_logger()

class DocumentConversionWorker(QThread):
    """文档转换工作线程"""

    # 信号：转换完成
    conversion_finished = Signal(
        list, dict, bool, str, dict
    )  # converted_files, file_mapping, success, error_msg, excel_result
    # 状态更新信号
    status_updated = Signal(str)

    def __init__(self, file_paths: List[str], output_dir: str):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir

    def run(self):
        """执行文档转换"""
        try:
            self.status_updated.emit("正在转换文件格式，请稍候...")

            # 创建输出目录
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
            os.makedirs(self.output_dir)

            # 执行转换 - 修复：不传递参数，直接调用
            converted_files, file_mapping, excel_result = (
                self._convert_documents_and_copy_files()
            )

            if not converted_files and not excel_result.get("excel_data"):
                error_msg = "没有成功转换任何文件，请检查文件是否损坏或格式是否正确"
                self.conversion_finished.emit([], {}, False, error_msg, {})
                return

            self.conversion_finished.emit(
                converted_files, file_mapping, True, "", excel_result
            )

        except Exception as e:
            error_msg = f"文档转换失败: {str(e)}"
            self.conversion_finished.emit([], {}, False, error_msg, {})

    def _convert_documents_and_copy_files(
            self,
    ) -> Tuple[List[str], Dict[str, str], Dict[str, Any]]:
        """转换文档文件并复制其他文件到输出目录

        Returns:
            (转换后的文件路径列表, 文件名映射字典, Excel处理结果)
        """
        converted_files = []
        file_mapping = {}  # 转换后PDF文件名(无扩展名) -> 原始文件路径
        excel_result = {"excel_data": [], "type": None}  # Excel 特殊处理结果

        for file_path in self.file_paths:
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            ext_lower = ext.lower()

            # 发送当前文件转换状态
            self.status_updated.emit(f"正在转换文件: {filename}")

            if ext_lower in [".docx"]:
                # 转换Word文档
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"Word文档文件不存在或为空: {filename}")

                    output_pdf_path = os.path.join(self.output_dir, f"{name}.pdf")
                    docx_to_pdf(file_path, output_pdf_path)

                    # 检查转换结果
                    if (
                            not os.path.exists(output_pdf_path)
                            or os.path.getsize(output_pdf_path) == 0
                    ):
                        raise ValueError(f"Word文档转换后的PDF文件为空或未生成")

                    converted_files.append(output_pdf_path)
                    file_mapping[name] = file_path  # 建立映射关系
                    print(f"Word文档转换成功: {filename} -> {name}.pdf")
                    logger.info(f"Word文档转换成功: {filename} -> {name}.pdf")
                except Exception as e:
                    error_msg = f"Word文档转换失败 {filename}: {str(e)}"
                    print(error_msg)
                    logger.error(error_msg)
                    continue

            elif ext_lower in [".xls", ".xlsx"]:
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"Excel文档文件不存在或为空: {filename}")
                    # 处理 Excel 文件，返回处理结果信息
                    current_excel_result = self._process_excel_file(file_path, name)
                    # 将处理结果添加到转换文件列表
                    if current_excel_result:
                        converted_files.extend(current_excel_result.get("files", []))
                        # 为每个文件建立映射关系
                        for result_file in current_excel_result.get("files", []):
                            result_name = os.path.splitext(
                                os.path.basename(result_file)
                            )[0]
                            file_mapping[result_name] = file_path

                        # 合并 Excel 数据
                        if current_excel_result.get("excel_data"):
                            excel_result["excel_data"].extend(
                                current_excel_result["excel_data"]
                            )
                            excel_result["type"] = current_excel_result.get("type")

                    print(f"Excel文档处理成功: {filename}")
                    logger.info(f"Excel文档处理成功: {filename}")
                except Exception as e:
                    error_msg = f"Excel文档处理失败 {filename}: {str(e)}"
                    print(error_msg)
                    logger.error(error_msg)
                    continue

            elif ext_lower in [".rtf"]:
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"RTF文档文件不存在或为空: {filename}")

                    output_pdf_path = os.path.join(self.output_dir, f"{name}.pdf")
                    rtf_to_pdf(file_path, output_pdf_path)

                    # 检查转换结果
                    if (
                            not os.path.exists(output_pdf_path)
                            or os.path.getsize(output_pdf_path) == 0
                    ):
                        raise ValueError(f"RTF文档转换后的PDF文件为空或未生成")

                    converted_files.append(output_pdf_path)
                    file_mapping[name] = file_path  # 建立映射关系
                    print(f"RTF文档转换成功: {filename} -> {name}.pdf")
                    logger.info(f"RTF文档转换成功: {filename} -> {name}.pdf")
                except Exception as e:
                    error_msg = f"RTF文档转换失败 {filename}: {str(e)}"
                    print(error_msg)
                    logger.error(error_msg)
                    continue

            elif ext_lower in [".pdf", ".jpg", ".jpeg", ".png"]:
                # 直接复制PDF和图片文件
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"文件不存在或为空: {filename}")

                    dest_path = os.path.join(self.output_dir, filename)
                    shutil.copy2(file_path, dest_path)

                    # 检查复制结果
                    if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
                        raise ValueError(f"文件复制失败或复制后文件为空: {filename}")

                    converted_files.append(dest_path)
                    # 对于直接复制的文件，也建立映射关系
                    file_mapping[name] = file_path
                    print(f"文件复制成功: {filename}")
                    logger.info(f"文件复制成功: {filename}")
                except Exception as e:
                    error_msg = f"文件复制失败 {filename}: {str(e)}"
                    print(error_msg)
                    logger.error(error_msg)
                    continue

        return converted_files, file_mapping, excel_result

    def _process_excel_file(self, file_path: str, base_name: str) -> dict:
        """
        处理 Excel 文件的完整流程

        参数：
            file_path: Excel 文件路径
            base_name: 基础文件名（不含扩展名）

        返回：
            包含处理结果的字典
        """
        result = {"files": [], "type": None, "data": None, "excel_data": []}

        # 创建临时工作目录
        excel_work_dir = os.path.join(self.output_dir, f"excel_work_{base_name}")
        os.makedirs(excel_work_dir, exist_ok=True)

        # 第一步：如果是 .xls 文件，转换为 .xlsx
        xlsx_file = file_path
        if file_path.lower().endswith(".xls"):
            self.status_updated.emit(f"正在转换 .xls 为 .xlsx: {base_name}")
            xlsx_file = os.path.join(excel_work_dir, f"{base_name}.xlsx")
            convert_xls_to_xlsx(file_path, xlsx_file)
            print(f"已转换 .xls 为 .xlsx: {xlsx_file}")

        # 第二步：拆分多个 sheet
        self.status_updated.emit(f"正在拆分工作表: {base_name}")
        split_dir = os.path.join(excel_work_dir, "split_sheets")
        os.makedirs(split_dir, exist_ok=True)
        split_excel_sheets(xlsx_file, split_dir)

        # 获取所有拆分后的 xlsx 文件
        all_split_files = [
            os.path.join(split_dir, f)
            for f in os.listdir(split_dir)
            if f.endswith(".xlsx")
        ]

        # 过滤掉空的 Excel 文件
        split_files = []
        for file in all_split_files:
            if self._is_excel_empty(file):
                print(f"跳过空的 Excel 文件: {os.path.basename(file)}")
                # 删除空文件
                try:
                    os.remove(file)
                except:
                    pass
            else:
                split_files.append(file)

        print(
            f"拆分后有效文件数量: {len(split_files)} (总共 {len(all_split_files)} 个)"
        )

        # 如果没有有效文件，直接返回
        if not split_files:
            print(f"警告: Excel 文件 '{base_name}' 的所有工作表都为空，跳过处理")
            self.status_updated.emit(f"跳过空的 Excel 文件: {base_name}")
            return result

        # 第三步：将 xlsx 转换为图片用于布局检测
        self.status_updated.emit(f"正在转换为图片进行布局分析: {base_name}")
        image_dir = os.path.join(excel_work_dir, "images")
        os.makedirs(image_dir, exist_ok=True)
        convert_excel_to_images(split_files, image_dir)

        # 第四步：对每个 sheet 进行布局检测和处理
        for split_file in split_files:
            sheet_name = os.path.splitext(os.path.basename(split_file))[0]
            image_file = os.path.join(image_dir, f"{sheet_name}.png")

            if not os.path.exists(image_file):
                print(f"图片文件不存在，跳过: {image_file}")
                continue

            self.status_updated.emit(f"正在检测布局类型: {sheet_name}")
            layout_type = detect_excel_layout(image_file)
            print(f"检测到布局类型: {layout_type} for {sheet_name}")

            try:
                layout_num = int(layout_type.strip())
            except:
                print(f"无法解析布局类型，默认为类型0: {layout_type}")
                layout_num = 0

            if layout_num == 1:
                # 扁平式布局 - 提取图片并直接进行数据提取
                self.status_updated.emit(f"处理扁平式布局: {sheet_name}")
                image_files = self._process_flat_layout(
                    split_file, sheet_name, excel_work_dir
                )
                result["files"].extend(image_files)

                # 直接对图片进行数据提取
                if image_files:
                    self.status_updated.emit(f"正在提取扁平式布局数据: {sheet_name}")
                    flat_data = self._extract_flat_layout_data(image_files)
                    print(f"扁平式布局提取数据数量: {flat_data}")
                    for item in flat_data:
                        item["源文件"] = file_path
                    result["excel_data"].extend(flat_data)

                result["type"] = "flat"

            elif layout_num == 2:
                # 主表+子表布局 - 暂时跳过
                self.status_updated.emit(f"跳过主表+子表布局: {sheet_name}")
                print(f"布局类型2暂未实现，跳过: {sheet_name}")
                result["type"] = "master_detail"
                continue

            elif layout_num == 3:
                # 分块布局 - 直接使用提取的 markdown 数据
                self.status_updated.emit(f"处理分块布局: {sheet_name}")
                result_data = self._process_block_layout(
                    split_file, sheet_name, excel_work_dir
                )
                if result_data:
                    result["files"].append(result_data["file"])

                    # 直接处理 markdown 数据提取结构化信息
                    self.status_updated.emit(f"正在提取分块布局数据: {sheet_name}")
                    block_data = self._extract_block_layout_data(
                        result_data["markdown"], file_path
                    )
                    result["excel_data"].extend(block_data)
                result["type"] = "block"

            else:
                print(f"未知布局类型: {layout_num}，默认使用分块布局处理")
                result_data = self._process_block_layout(
                    split_file, sheet_name, excel_work_dir
                )
                if result_data:
                    result["files"].append(result_data["file"])

                    # 直接处理 markdown 数据提取结构化信息
                    self.status_updated.emit(f"正在提取数据: {sheet_name}")
                    block_data = self._extract_block_layout_data(
                        result_data["markdown"]
                    )
                    result["excel_data"].extend(block_data)
                result["type"] = "block"

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
        self.status_updated.emit(f"正在分析表头: {sheet_name}")
        rows = read_excel_first_20_rows(excel_file)
        header_index = int(determine_header_index(rows))
        print(f"表头索引: {header_index} for {sheet_name}")

        # 按行切分
        self.status_updated.emit(f"正在切分表格: {sheet_name}")
        split_output_dir = os.path.join(work_dir, f"flat_split_{sheet_name}")
        os.makedirs(split_output_dir, exist_ok=True)
        split_excel_by_rows_with_header(excel_file, split_output_dir, header_index + 1, rows_per_file=5)

        # 格式化所有切分后的文件
        self.status_updated.emit(f"正在格式化表格: {sheet_name}")
        formatted_files = format_excel_files_in_directory(split_output_dir)

        # 转换为图片
        self.status_updated.emit(f"正在转换为图片: {sheet_name}")
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
        self.status_updated.emit(f"正在格式化和转换: {sheet_name}")
        image_output = os.path.join(work_dir, f"block_image_{sheet_name}.png")
        format_excel_and_convert_to_image(excel_file, image_output)

        # 使用大模型提取数据
        self.status_updated.emit(f"正在提取数据: {sheet_name}")
        markdown_content = extract_excel_data_to_markdown(image_output)
        print(f"提取的 Markdown 内容长度: {len(markdown_content)} for {sheet_name}")

        return {
            "file": image_output,
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

        # 连接状态更新信号，将子worker的信号转发到当前worker
        worker.status_updated.connect(lambda msg: self.status_updated.emit(msg))

        try:
            # 直接调用提取方法
            extracted_data = worker.extract_data_from_pdf(image_files)
            print(f"扁平式布局数据提取完成，共 {len(extracted_data)} 条记录")
            return extracted_data
        except Exception as e:
            error_msg = f"扁平式布局数据提取失败: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            return []

    def _is_excel_empty(self, file_path: str) -> bool:
        """
        检查 Excel 文件是否为空（没有数据或只有空行）

        参数：
            file_path: Excel 文件路径

        返回：
            如果文件为空返回 True，否则返回 False
        """
        try:
            import openpyxl

            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active

            # 检查是否有任何非空单元格
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value is not None and str(cell.value).strip():
                        return False

            # 所有单元格都是空的
            return True

        except Exception as e:
            print(f"检查 Excel 文件是否为空时出错: {file_path}, 错误: {str(e)}")
            # 如果出错，假设文件不为空，继续处理
            return False

    def _extract_block_layout_data(
            self, markdown_content: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        从分块布局的 markdown 内容中提取结构化数据

        参数：
            markdown_content: Markdown 内容

        返回：
            提取的数据列表
        """
        import json

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

            for item in display_data:
                item["源文件"] = file_path
            print(f"分块布局数据提取完成，共 {len(display_data)} 条记录")
            return display_data

        except Exception as e:
            error_msg = f"分块布局数据提取失败: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            return []
