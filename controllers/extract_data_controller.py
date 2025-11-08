import json
import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any
from PySide6.QtCore import QThread, Signal

from utils.logger import get_file_conversion_logger, get_error_logger
from utils.mineru_parse import parse_doc
from utils.table_corrector_multi import TableCorrector
from utils.upload_file_to_oss import up_local_file

logger = get_file_conversion_logger()
error_logger = get_error_logger()

class ExtractDataWorker(QThread):
    """数据提取工作线程

    在后台线程中执行PDF文件解析和数据提取，避免阻塞主线程
    """

    # 信号：参数为文件名字符串, 提取的数据, 是否成功, 错误信息
    finished = Signal(str, list, bool, str)
    # 状态更新信号：用于更新UI提示文本
    status_updated = Signal(str)

    def __init__(
            self,
            file_paths: List[str],
            process_directory: bool = False,
            original_file_mapping: Dict[str, str] = None,
    ):
        """初始化工作线程

        Args:
            file_paths: 要处理的文件路径列表
            process_directory: 是否处理整个目录中的PDF文件
            original_file_mapping: 转换后PDF文件名到原始文件路径的映射
        """
        super().__init__()
        # 确保 file_paths 是列表
        if isinstance(file_paths, str):
            self.file_paths = [file_paths]
        elif isinstance(file_paths, list):
            self.file_paths = file_paths
        else:
            self.file_paths = list(file_paths)

        self.process_directory = process_directory
        self.original_file_mapping = original_file_mapping or {}

    def run(self) -> None:
        """在线程中执行耗时操作"""
        try:
            if self.process_directory:
                # 处理目录中的所有PDF文件
                pdf_files = []
                for file_path in self.file_paths:
                    if os.path.isdir(file_path):
                        # 如果是目录，找到其中所有PDF文件
                        for root, dirs, files in os.walk(file_path):
                            for file in files:
                                if file.lower().endswith(".pdf"):
                                    pdf_files.append(os.path.join(root, file))
                    elif file_path.lower().endswith(".pdf"):
                        pdf_files.append(file_path)

                if pdf_files:
                    filename_list = [
                        os.path.basename(file_path) for file_path in pdf_files
                    ]
                    filename_str = ", ".join(filename_list)
                    print(f"开始解析PDF文件: {pdf_files}")
                    object_keys = []
                    # TODO: 真实上传
                    for file_path in pdf_files:
                        try:
                            pdf_basename = os.path.splitext(
                                os.path.basename(file_path)
                            )[0]
                            original_file_path = self.original_file_mapping.get(
                                pdf_basename, file_path
                            )
                            object_key = 1
                            # object_key = up_local_file(original_file_path)
                            object_keys.append(object_key)
                            logger.info(
                                f"上传原始文件到OSS: {original_file_path} -> {object_key}"
                            )
                        except Exception as upload_error:
                            error_msg = f"上传文件 {os.path.basename(original_file_path)} 到OSS失败: {str(upload_error)}"
                            logger.error(error_msg)
                            self.finished.emit("", [], False, error_msg)
                            return
                    data = self._extract_data_from_pdf(pdf_files)
                    self.finished.emit(filename_str, data, True, "")
                else:
                    self.finished.emit("", [], False, "未找到PDF文件进行处理")
            else:
                # 原有逻辑：直接处理文件列表
                filename_list = [
                    os.path.basename(file_path) for file_path in self.file_paths
                ]
                filename_str = ", ".join(filename_list)
                print(f"开始解析PDF文件: {self.file_paths}")
                object_keys = []
                # TODO: 真实上传
                for file_path in self.file_paths:
                    try:
                        object_key = 1
                        # object_key = up_local_file(file_path)
                        object_keys.append(object_key)
                        logger.info(f"上传文件到OSS: {file_path} -> {object_key}")
                    except Exception as upload_error:
                        error_msg = f"上传文件 {os.path.basename(file_path)} 到OSS失败: {str(upload_error)}"
                        logger.error(error_msg)
                        self.finished.emit("", [], False, error_msg)
                        return
                data = self._extract_data_from_pdf(self.file_paths)
                self.finished.emit(filename_str, data, True, "")
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            print(f"Error: {error_msg}")
            logger.error(error_msg)
            self.finished.emit("", [], False, error_msg)

    def _extract_data_from_pdf(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """从PDF文件中提取数据

        Args:
            file_paths: PDF文件路径列表

        Returns:
            提取的数据列表
        """
        try:
            fixed_paths = []
            for path in file_paths:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"文件不存在: {path}")

                root, ext = os.path.splitext(path)
                if ext.isupper():
                    new_path = root + ext.lower()
                    if not os.path.exists(new_path):
                        try:
                            os.rename(path, new_path)
                        except OSError as e:
                            raise OSError(f"重命名文件失败 {path}: {str(e)}")
                    fixed_paths.append(new_path)
                else:
                    fixed_paths.append(path)

            file_paths = fixed_paths
            os.environ["MINERU_MODEL_SOURCE"] = "local"
        except Exception as e:
            error_msg = f"预处理文件失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

        try:
            # 解析PDF
            self.status_updated.emit("正在识别PDF，请稍候...")
            start_time = time.time()
            parse_doc(path_list=file_paths, output_dir="../output", backend="pipeline")
            end_time = time.time()
            print(f"PDF解析完成，耗时 {end_time - start_time:.2f} 秒")

            # 处理解析结果
            self.status_updated.emit("正在大模型提取结构，请稍候...")
            info_dict = self._process_parsed_results()
            print("完成PDF文件解析", info_dict)

            # 清理临时文件
            # self._cleanup_temp_files()

            # 构建返回数据
            return self._process_extracted_data(
                info_dict, file_paths, self.original_file_mapping
            )
        except Exception as e:
            error_msg = f"PDF解析失败: {str(e)}"
            logger.error(error_msg)
            # 确保清理临时文件
            try:
                self._cleanup_temp_files()
            except Exception as cleanup_error:
                logger.error(f"清理临时文件失败: {str(cleanup_error)}")
            raise Exception(error_msg)

    def _process_parsed_results(self) -> Dict[str, Any]:
        """处理解析结果

        Returns:
            处理后的信息字典
        """
        OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
        from dotenv import load_dotenv

        load_dotenv()
        API_KEY = os.getenv("DASHSCOPE_API_KEY1")
        corrector = TableCorrector(API_KEY)
        result = corrector.process_directory(OUTPUT_DIR)
        info_dict = result.get("info_dict", {})

        # 如果info_dict是字符串，尝试解析为JSON
        if isinstance(info_dict, str):
            try:
                info_dict = json.loads(info_dict)
            except json.JSONDecodeError:
                info_dict = {}

        return info_dict

    def _cleanup_temp_files(self) -> None:
        """清理临时文件"""
        if os.path.exists("./output"):
            shutil.rmtree("./output")
            print("删除临时文件夹 ./output")

    def _process_extracted_data(
            self,
            info_dict: Dict[str, Any],
            file_paths: List[str],
            original_file_mapping: Dict[str, str] = None,
    ) -> List[Dict[str, Any]]:
        """处理提取的数据"""
        # 建立文件名到完整路径的映射
        file_name_to_path = {}
        for file_path in file_paths:
            file_name = os.path.splitext(os.path.basename(file_path))[0]  # 去掉扩展名

            # 如果有原始文件映射，优先使用原始文件路径
            if original_file_mapping and file_name in original_file_mapping:
                file_name_to_path[file_name] = original_file_mapping[file_name]
            else:
                file_name_to_path[file_name] = file_path

        display_data = []
        for file_name, records in info_dict.items():
            # 使用映射查找对应的文件路径
            source_file = file_name_to_path.get(file_name, "未知文件")

            for record in records:
                amount = record.get("金额", "")
                if amount:
                    amount_str = (
                        str(amount)
                        .strip()
                        .replace("¥", "")
                        .replace("$", "")
                        .replace(",", "")
                    )
                    amount_value = float(amount_str)
                    if abs(amount_value) < 0.001:
                        continue
                record["源文件"] = source_file
                display_data.append(record)

        return display_data
