import os
import shutil
from typing import List, Tuple, Dict, Any
from PySide6.QtCore import QThread, Signal

from utils.file_to_pdf import docx_to_pdf, rtf_to_pdf
from utils.logger import get_file_conversion_logger, get_error_logger, upload_all_logs
from controllers.excel_process_controller import ExcelProcessHandler

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

    def __init__(self, file_paths: List[str], output_dir: str, original_file_mapping: Dict[str, str] = None):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.original_file_mapping = original_file_mapping or {}  # 临时文件路径 -> 原始文件路径

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
                error_msg = "请重新分析文件，模型没有提取到有效数据。"
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
        excel_files = []  # 收集所有Excel文件

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
                    # 使用原始文件路径建立映射
                    original_path = self.original_file_mapping.get(file_path, file_path)
                    file_mapping[name] = original_path
                    print(f"Word文档转换成功: {filename} -> {name}.pdf")
                except Exception as e:
                    error_msg = f"Word文档转换失败 {filename}: {str(e)}"
                    print(error_msg)
                    error_logger.error(error_msg)
                    continue

            elif ext_lower in [".xls", ".xlsx"]:
                # Excel文件先收集，稍后批量处理
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"Excel文档文件不存在或为空: {filename}")
                    excel_files.append((file_path, name))
                    print(f"收集Excel文件: {filename}")
                except Exception as e:
                    error_msg = f"Excel文件检查失败 {filename}: {str(e)}"
                    print(error_msg)
                    error_logger.error(error_msg)
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
                    # 使用原始文件路径建立映射
                    original_path = self.original_file_mapping.get(file_path, file_path)
                    file_mapping[name] = original_path
                    print(f"RTF文档转换成功: {filename} -> {name}.pdf")
                except Exception as e:
                    error_msg = f"RTF文档转换失败 {filename}: {str(e)}"
                    print(error_msg)
                    error_logger.error(error_msg)
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
                    # 对于直接复制的文件，也建立映射关系，使用原始文件路径
                    original_path = self.original_file_mapping.get(file_path, file_path)
                    file_mapping[name] = original_path
                    print(f"文件复制成功: {filename}")
                except Exception as e:
                    error_msg = f"文件复制失败 {filename}: {str(e)}"
                    print(error_msg)
                    error_logger.error(error_msg)
                    continue

        # 批量处理所有Excel文件
        if excel_files:
            print(f"\n{'=' * 60}")
            print(f"开始批量处理 {len(excel_files)} 个Excel文件")
            print(f"{'=' * 60}\n")

            # 使用 ExcelProcessHandler 处理Excel文件，传递原始文件映射
            excel_handler = ExcelProcessHandler(
                self.output_dir,
                self.status_updated,
                original_file_mapping=self.original_file_mapping
            )
            batch_result = excel_handler.process_excel_files_batch(excel_files)

            if batch_result:
                converted_files.extend(batch_result.get("files", []))

                # 建立映射关系
                for result_file in batch_result.get("files", []):
                    result_name = os.path.splitext(os.path.basename(result_file))[0]
                    # 从批量结果中找到对应的原始文件
                    original_file = batch_result.get("file_mapping", {}).get(
                        result_name
                    )
                    if original_file:
                        file_mapping[result_name] = original_file

                # 合并Excel数据
                if batch_result.get("excel_data"):
                    excel_result["excel_data"].extend(batch_result["excel_data"])
                    excel_result["type"] = batch_result.get("type")

                print(f"\n{'=' * 60}")
                print(
                    f"Excel批量处理完成: 提取 {len(batch_result.get('excel_data', []))} 条数据"
                )
                print(f"{'=' * 60}\n")

        return converted_files, file_mapping, excel_result
