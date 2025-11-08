import os
import shutil
from typing import List, Tuple, Dict
from PySide6.QtCore import QThread, Signal

from utils.file_to_pdf import excel_to_pdf, docx_to_pdf, rtf_to_pdf
from utils.logger import get_file_conversion_logger, get_error_logger

# 使用统一的日志系统（与 upload_controller 共享日志文件）
logger = get_file_conversion_logger()
error_logger = get_error_logger()


class DocumentConversionWorker(QThread):
    """文档转换工作线程"""

    # 信号：转换完成
    conversion_finished = Signal(
        list, dict, bool, str
    )  # converted_files, file_mapping, success, error_msg
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
            converted_files, file_mapping = self._convert_documents_and_copy_files()

            if not converted_files:
                error_msg = "没有成功转换任何文件，请检查文件是否损坏或格式是否正确"
                self.conversion_finished.emit([], {}, False, error_msg)
                return

            self.conversion_finished.emit(converted_files, file_mapping, True, "")

        except Exception as e:
            error_msg = f"文档转换失败: {str(e)}"
            self.conversion_finished.emit([], {}, False, error_msg)

    def _convert_documents_and_copy_files(self) -> Tuple[List[str], Dict[str, str]]:
        """转换文档文件并复制其他文件到输出目录

        Returns:
            (转换后的文件路径列表, 文件名映射字典)
        """
        converted_files = []
        file_mapping = {}  # 转换后PDF文件名(无扩展名) -> 原始文件路径

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

                    output_pdf_path = excel_to_pdf(file_path, self.output_dir)

                    # 检查转换结果
                    if (
                            not os.path.exists(output_pdf_path)
                            or os.path.getsize(output_pdf_path) == 0
                    ):
                        raise ValueError(f"Excel文档转换后的PDF文件为空或未生成")

                    converted_files.append(output_pdf_path)
                    file_mapping[name] = file_path  # 建立映射关系
                    print(f"Excel文档转换成功: {filename} -> {name}.pdf")
                    logger.info(f"Excel文档转换成功: {filename} -> {name}.pdf")
                except Exception as e:
                    error_msg = f"Excel文档转换失败 {filename}: {str(e)}"
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

        return converted_files, file_mapping
