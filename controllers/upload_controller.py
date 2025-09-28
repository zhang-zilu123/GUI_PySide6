"""
上传功能控制器
处理文件上传相关的业务逻辑
"""
import os
import shutil
import json
import time
import logging

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from PySide6.QtWidgets import QFileDialog, QMessageBox, QHBoxLayout, QPushButton
from PySide6.QtCore import QObject, Signal, QThread, Qt

from datetime import datetime
from data.temp_data import get_data
from utils.common import get_filename_list
from utils.mineru_parse import parse_doc
from utils.model_md_to_json import extract_info_from_md
from config.config import EXTRA_FIELD, API_KEY
from utils.model_translate import translate_json
from utils.upload_file_to_oss import up_local_file
from utils.table_corrector_multi import TableCorrector
from utils.file_to_pdf import excel_to_pdf, docx_to_pdf, rtf_to_pdf

os.makedirs('./log', exist_ok=True)
current_time = datetime.now().strftime('%Y%m%d-%H%M')
log_filename = f'./log/{current_time}-上传文件.log'
logger = logging.getLogger("upload")
handler = logging.FileHandler(log_filename, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

with open('./device_id.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    logger.info(f'device_id:{content}')


class ExtractDataWorker(QThread):
    """数据提取工作线程
    
    在后台线程中执行PDF文件解析和数据提取，避免阻塞主线程
    """

    # 信号：参数为文件名字符串, 提取的数据, 是否成功, 错误信息
    finished = Signal(str, list, bool, str)

    def __init__(self, file_paths: List[str], process_directory: bool = False,
                 original_file_mapping: Dict[str, str] = None):
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
                                if file.lower().endswith('.pdf'):
                                    pdf_files.append(os.path.join(root, file))
                    elif file_path.lower().endswith('.pdf'):
                        pdf_files.append(file_path)

                if pdf_files:
                    filename_list = [os.path.basename(file_path) for file_path in pdf_files]
                    filename_str = ", ".join(filename_list)
                    print(f"开始解析PDF文件: {pdf_files}")
                    object_keys = []
                    # TODO: 真实上传
                    for file_path in pdf_files:
                        try:
                            # object_key = up_local_file(file_path)
                            object_key = 0
                            object_keys.append(object_key)
                            logger.info(f'上传文件到OSS: {file_path} -> {object_key}')
                        except Exception as upload_error:
                            error_msg = f"上传文件 {os.path.basename(file_path)} 到OSS失败: {str(upload_error)}"
                            logger.error(error_msg)
                            self.finished.emit("", [], False, error_msg)
                            return
                    # up_local_file(log_filename)
                    print('上传到OSS完成:', log_filename)
                    data = self._extract_data_from_pdf(pdf_files)
                    self.finished.emit(filename_str, data, True, "")
                else:
                    self.finished.emit("", [], False, "未找到PDF文件进行处理")
            else:
                # 原有逻辑：直接处理文件列表
                filename_list = [os.path.basename(file_path) for file_path in self.file_paths]
                filename_str = ", ".join(filename_list)
                print(f"开始解析PDF文件: {self.file_paths}")
                object_keys = []
                # TODO: 真实上传
                for file_path in self.file_paths:
                    try:
                        # object_key = up_local_file(file_path)
                        object_key = 0
                        object_keys.append(object_key)
                        logger.info(f'上传文件到OSS: {file_path} -> {object_key}')
                    except Exception as upload_error:
                        error_msg = f"上传文件 {os.path.basename(file_path)} 到OSS失败: {str(upload_error)}"
                        logger.error(error_msg)
                        self.finished.emit("", [], False, error_msg)
                        return
                # up_local_file(log_filename)
                print('上传到OSS完成:', log_filename)
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
            os.environ['MINERU_MODEL_SOURCE'] = 'local'
            print(f'开始解析PDF文件: {file_paths}')
        except Exception as e:
            error_msg = f"预处理文件失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

        try:
            # 解析PDF
            start_time = time.time()
            parse_doc(path_list=file_paths, output_dir="./output", backend="pipeline")
            end_time = time.time()
            print(f"PDF解析完成，耗时 {end_time - start_time:.2f} 秒")

            # 处理解析结果
            info_dict = self._process_parsed_results()
            print('完成PDF文件解析', info_dict)

            # 清理临时文件
            self._cleanup_temp_files()

            # 构建返回数据
            return self._process_extracted_data(info_dict, file_paths, self.original_file_mapping)
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
        if os.path.exists('./output'):
            shutil.rmtree('./output')
            print('删除临时文件夹 ./output')

    def _process_extracted_data(self, info_dict: Dict[str, Any],
                                file_paths: List[str], original_file_mapping: Dict[str, str] = None) -> List[
        Dict[str, Any]]:
        """处理提取的数据
        
        Args:
            info_dict: 提取的信息字典
            file_paths: 文件路径列表
            original_file_mapping: 转换后PDF文件名到原始文件路径的映射
            
        Returns:
            处理后的数据列表
        """
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
                record['源文件'] = source_file
                display_data.append(record)

        return display_data


class UploadController(QObject):
    """上传功能控制器
    
    负责处理文件上传和数据提取相关的业务逻辑：
    - 文件选择和验证
    - 拖拽文件处理
    - PDF数据提取
    - UI状态管理
    """

    # 信号定义
    file_processed = Signal()
    processing_started = Signal()
    processing_finished = Signal()

    def __init__(self, view, data_manager):
        """初始化上传控制器
        
        Args:
            view: 上传视图对象
            data_manager: 数据管理器
        """
        super().__init__()
        self.view = view
        self.data_manager = data_manager
        self.uploaded_files: List[str] = []
        self.current_workers: List[ExtractDataWorker] = []
        self._setup_controller()

    def _setup_controller(self) -> None:
        """设置控制器"""
        self._connect_signals()
        self._reset_to_initial_state()

    def _connect_signals(self) -> None:
        """连接视图信号"""
        self.view.upload_frame.mousePressEvent = self._on_upload_area_clicked
        self.view.upload_requested.connect(self._on_upload_requested)
        self.view.clear_requested.connect(self.clear_file_list)
        self.view.analyze_requested.connect(self._on_analyze_requested)
        self.view.files_dropped.connect(self._on_files_dropped)

    def _on_upload_area_clicked(self, event) -> None:
        """处理上传区域点击事件
        
        Args:
            event: 鼠标事件
        """
        self._open_file_dialog()

    def _on_upload_requested(self) -> None:
        """处理上传请求"""
        self._open_file_dialog()

    def _on_files_dropped(self, file_paths: List[str]) -> None:
        """处理拖拽文件事件
        
        Args:
            file_paths: 拖拽的文件路径列表
        """
        self._process_selected_files(file_paths)

    def _on_analyze_requested(self) -> None:
        """处理分析请求"""
        if not self.uploaded_files:
            reply = QMessageBox.warning(
                self.view, 
                "提示", 
                "请先上传文件后再进行分析",
                QMessageBox.Ok | QMessageBox.Cancel
            )
            if reply == QMessageBox.Ok:
                # 确保按钮处于可用状态，允许用户重新上传
                self._reset_button_states()
            return

        self._start_analysis()

    def _open_file_dialog(self) -> None:
        """打开文件选择对话框"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.view,
            "选择文件",
            "",
            "支持的文件 (*.pdf *.jpg *.jpeg *.png *.docx *.xls *.xlsx *.rtf);;所有文件 (*.*)"
        )

        if file_paths:
            self._process_selected_files(file_paths)

    def _process_selected_files(self, file_paths: List[str]) -> None:
        """处理选择的文件
        
        Args:
            file_paths: 选择的文件路径列表
        """
        valid_files = []
        invalid_files = []

        for file_path in file_paths:
            if self._validate_file(file_path):
                valid_files.append(file_path)
                # if not self._is_file_already_uploaded(file_path):
                #     valid_files.append(file_path)
                # else:
                #     self._show_file_exists_message(file_path)
            else:
                invalid_files.append(file_path)

        self._handle_file_validation_results(valid_files, invalid_files)

    def _validate_file(self, file_path: str) -> bool:
        """验证文件格式

        Args:
            file_path: 文件路径

        Returns:
            文件是否有效
        """
        try:
            if not os.path.isfile(file_path):
                return False
            
            # 检查文件是否可读
            try:
                with open(file_path, 'rb') as f:
                    # 尝试读取文件头部以确认文件完整性
                    f.read(1024)
            except (IOError, OSError):
                return False
            
            _, ext = os.path.splitext(file_path)
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.xls', '.xlsx', '.rtf']
            return ext.lower() in valid_extensions
        except Exception as e:
            print(f"文件验证异常 {file_path}: {str(e)}")
            return False

    def _is_file_already_uploaded(self, file_path: str) -> bool:
        """检查文件是否已经上传

        Args:
            file_path: 文件路径

        Returns:
            文件是否已上传
        """
        file_name = os.path.basename(file_path)

        # 检查当前上传列表中是否有相同的文件（按文件名比较）
        for uploaded_file in self.uploaded_files:
            if os.path.basename(uploaded_file) == file_name:
                return True

        # 检查历史上传的文件名
        uploaded_file_names = self._get_uploaded_file_names()
        now_file_names = self._get_now_file_names()

        return file_name in now_file_names or file_name in uploaded_file_names

    def _get_uploaded_file_names(self) -> List[str]:
        """获取已上传的文件名列表

        Returns:
            已上传的文件名列表
        """
        if not hasattr(self.data_manager, 'uploaded_file_name') or not self.data_manager.uploaded_file_name:
            return []
        if isinstance(self.data_manager.uploaded_file_name, str):
            return [name.strip() for name in self.data_manager.uploaded_file_name.split(',')]
        return []

    def _get_now_file_names(self) -> List[str]:
        """获取当前文件名列表

        Returns:
            当前文件名列表
        """
        if isinstance(self.data_manager.file_name, str):
            return [name.strip() for name in self.data_manager.file_name.split(',')]
        return []

    def _show_file_exists_message(self, file_path: str) -> None:
        """显示文件已存在的消息

        Args:
            file_path: 文件路径
        """
        file_name = os.path.basename(file_path)
        QMessageBox.information(
            self.view,
            "文件已存在",
            f"文件 {file_name} 本次已上传，不能重复上传"
        )

    def _handle_file_validation_results(self, valid_files: List[str], invalid_files: List[str]) -> None:
        """处理文件验证结果

        Args:
            valid_files: 有效文件列表
            invalid_files: 无效文件列表
        """
        if invalid_files:
            self._show_invalid_files_message(invalid_files)
        if valid_files:
            self._add_files_to_list(valid_files)

    def _show_invalid_files_message(self, invalid_files: List[str]) -> None:
        """显示无效文件消息

        Args:
            invalid_files: 无效文件列表
        """
        invalid_names = [os.path.basename(fp) for fp in invalid_files]
        reply = QMessageBox.warning(
            self.view,
            "文件格式错误",
            f"以下文件格式不支持:\n{', '.join(invalid_names)}\n\n请选择PDF, JPG, PNG, DOCX, XLS, XLSX, RTF格式的文件。\n\n点击确定重新选择文件。",
            QMessageBox.Ok | QMessageBox.Cancel
        )
        if reply == QMessageBox.Ok:
            # 确保按钮处于可用状态，允许用户重新上传
            self._reset_button_states()

    # ==================== 文件列表管理 ====================
    def _add_files_to_list(self, file_paths):
        """添加文件到列表"""
        if not file_paths:
            return

        self.uploaded_files.extend(file_paths)
        self._rebuild_file_display()
        self._update_ui_state()
        self._update_instruction_text()

    def _update_instruction_text(self):
        """更新说明文字"""
        file_count = len(self.uploaded_files)
        self.view.instruction.setText(
            f"已选择 {file_count} 个文件，可点击'继续上传'增加文件或点击'开始分析'提取数据"
        )

    def _rebuild_file_display(self):
        """重新构建文件显示"""
        self._clear_file_layout()
        for file_path in self.uploaded_files:
            self._create_file_item(file_path)

    def _clear_file_layout(self):
        """清除文件布局中的所有控件"""
        while self.view.files_layout.count():
            child = self.view.files_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout_recursive(child.layout())

    def _clear_layout_recursive(self, layout):
        """递归清除布局"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout_recursive(child.layout())

    def _create_file_item(self, file_path):
        """创建文件项显示"""
        file_layout = QHBoxLayout()
        file_layout.setContentsMargins(0, 0, 0, 0)
        # 文件名按钮
        file_button = self._create_file_button(file_path)
        delete_button = self._create_delete_button(file_path)
        file_layout.addWidget(file_button)
        file_layout.addStretch()
        file_layout.addWidget(delete_button)

        self.view.files_layout.addLayout(file_layout)

    def _create_file_button(self, file_path):
        """创建文件按钮"""
        file_button = QPushButton(os.path.basename(file_path))
        file_button.setToolTip(file_path)
        file_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: none;
                background-color: transparent;
                border-bottom: 1px solid #eee;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        file_button.setCursor(Qt.PointingHandCursor)
        return file_button

    def _create_delete_button(self, file_path):
        """创建删除按钮"""
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.setStyleSheet("""
            QPushButton {
                color: #999999;
                background: transparent;
                border: none;
                font-size: 20px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                color: #ff4d4f;
            }
        """)
        delete_button.setCursor(Qt.PointingHandCursor)
        delete_button.clicked.connect(lambda: self._remove_file(file_path))
        return delete_button

    def _remove_file(self, file_path):
        """删除指定文件"""
        if file_path in self.uploaded_files:
            self.uploaded_files.remove(file_path)
            self._rebuild_file_display()
            self._update_ui_state()

            if self.uploaded_files:
                self._update_instruction_text()
            else:
                self._reset_to_initial_state()

    def clear_file_list(self):
        """清空文件列表"""
        self.uploaded_files.clear()
        self._clear_file_layout()
        self._reset_to_initial_state()

    # ==================== UI 状态管理 ====================
    def _update_ui_state(self):
        """更新界面状态"""
        has_files = len(self.uploaded_files) > 0

        if has_files:
            self._show_file_list_state()
        else:
            self._reset_to_initial_state()

    def _show_file_list_state(self):
        """显示文件列表状态"""
        self.view.upload_frame.setVisible(False)
        self.view.scroll_area.setVisible(True)
        self.view.files_widget.setVisible(True)
        self.view.analyze_button.setVisible(True)
        self.view.clear_button.setVisible(True)
        self.view.upload_button.setText("继续上传")

    def _reset_to_initial_state(self):
        """重置到初始状态"""
        self.view.upload_frame.setVisible(True)
        self.view.scroll_area.setVisible(False)
        self.view.files_widget.setVisible(False)
        self.view.analyze_button.setVisible(False)
        self.view.clear_button.setVisible(False)
        self.view.upload_button.setText("上传")
        self.view.instruction.setText("请上传需要审核的数据文件")
        self._reset_upload_info_display()

    def _reset_upload_info_display(self):
        """重置上传信息显示"""
        self.view.upload_info.setText("""
            <div style="font-size: 48px;">📁</div>
        <div style="font-size: 16px; color: #888;">点击或拖拽文件到此处上传</div>
        <div style="font-size: 12px; color: #888;">（不建议上传中英混杂的文件，容易出现解析错误）</div>   
        <div style="font-size: 12px; color: #aaa;">支持格式: pdf、jpg、jpeg、png、docx、xls、xlsx、rtf</div>
        """)

    def _set_processing_state(self, processing):
        """设置处理状态"""
        enabled = not processing
        self.view.upload_button.setEnabled(enabled)
        self.view.analyze_button.setEnabled(enabled)
        self.view.clear_button.setEnabled(enabled)
        self.view.upload_frame.setEnabled(enabled)

    # ==================== 文件类型检测 ====================
    def _has_document_files(self, file_paths: List[str]) -> bool:
        """检测文件列表中是否包含文档文件

        Args:
            file_paths: 文件路径列表

        Returns:
            如果包含docx, xls, xlsx, rtf文件则返回True
        """
        document_extensions = ['.docx', '.xls', '.xlsx', '.rtf']
        for file_path in file_paths:
            _, ext = os.path.splitext(file_path)
            if ext.lower() in document_extensions:
                return True
        return False

    def _separate_files_by_type(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """按文件类型分离文件

        Args:
            file_paths: 文件路径列表

        Returns:
            包含不同类型文件的字典
        """
        document_files = []
        pdf_image_files = []

        document_extensions = ['.docx', '.xls', '.xlsx', '.rtf']
        pdf_image_extensions = ['.pdf', '.jpg', '.jpeg', '.png']

        for file_path in file_paths:
            _, ext = os.path.splitext(file_path)
            ext_lower = ext.lower()

            if ext_lower in document_extensions:
                document_files.append(file_path)
            elif ext_lower in pdf_image_extensions:
                pdf_image_files.append(file_path)

        return {
            'documents': document_files,
            'pdf_images': pdf_image_files
        }

    # ==================== 数据分析处理 ====================
    def _start_analysis(self):
        """开始分析处理"""
        self._set_processing_state(True)
        self.processing_started.emit()
        self.view.title.setText("正在提取识别中，请稍候...")

        # 检查是否需要文档转换
        if self._has_document_files(self.uploaded_files):
            self._start_document_conversion_analysis()
        else:
            self._start_direct_analysis()

    def _start_direct_analysis(self):
        """开始直接分析（原有流程）"""
        worker = ExtractDataWorker(self.uploaded_files.copy())
        worker.finished.connect(self._on_worker_finished)
        worker.start()
        self.current_workers.append(worker)

    def _start_document_conversion_analysis(self):
        """开始文档转换分析"""
        try:
            # 创建输出目录
            output_dir = os.path.join(os.getcwd(), "converted_files")
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir)

            # 转换文档并复制文件
            converted_files, file_mapping = self._convert_documents_and_copy_files(self.uploaded_files, output_dir)

            if not converted_files:
                error_msg = "没有成功转换任何文件，请检查文件是否损坏或格式是否正确"
                self._handle_extraction_error(error_msg)
                return

            # 使用转换后的目录进行分析（处理目录中所有PDF文件）
            worker = ExtractDataWorker([output_dir], process_directory=True, original_file_mapping=file_mapping)
            worker.finished.connect(self._on_worker_finished)
            worker.start()
            self.current_workers.append(worker)

        except Exception as e:
            error_msg = f"文档转换失败: {str(e)}"
            print(f"Error: {error_msg}")
            logger.error(error_msg)
            self._handle_extraction_error(error_msg)

    def _convert_documents_and_copy_files(self, file_paths: List[str], output_dir: str) -> Tuple[
        List[str], Dict[str, str]]:
        """转换文档文件并复制其他文件到输出目录

        Args:
            file_paths: 原始文件路径列表
            output_dir: 输出目录

        Returns:
            (转换后的文件路径列表, 文件名映射字典)
        """
        converted_files = []
        file_mapping = {}  # 转换后PDF文件名(无扩展名) -> 原始文件路径

        for file_path in file_paths:
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            ext_lower = ext.lower()

            if ext_lower in ['.docx']:
                # 转换Word文档
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"Word文档文件不存在或为空: {filename}")
                    
                    output_pdf_path = os.path.join(output_dir, f"{name}.pdf")
                    docx_to_pdf(file_path, output_pdf_path)
                    
                    # 检查转换结果
                    if not os.path.exists(output_pdf_path) or os.path.getsize(output_pdf_path) == 0:
                        raise ValueError(f"Word文档转换后的PDF文件为空或未生成")
                    
                    converted_files.append(output_pdf_path)
                    file_mapping[name] = file_path  # 建立映射关系
                    print(f"Word文档转换成功: {filename} -> {name}.pdf")
                    logger.info(f"Word文档转换成功: {filename} -> {name}.pdf")
                except Exception as e:
                    error_msg = f"Word文档转换失败 {filename}: {str(e)}"
                    print(error_msg)
                    logger.error(error_msg)
                    # 转换失败时跳过该文件，不复制原文件，因为mineru无法处理doc/docx
                    continue

            elif ext_lower in ['.xls', '.xlsx']:
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"Excel文档文件不存在或为空: {filename}")
                    
                    output_pdf_path = excel_to_pdf(file_path, output_dir)
                    
                    # 检查转换结果
                    if not os.path.exists(output_pdf_path) or os.path.getsize(output_pdf_path) == 0:
                        raise ValueError(f"Excel文档转换后的PDF文件为空或未生成")
                    
                    converted_files.append(output_pdf_path)
                    file_mapping[name] = file_path  # 建立映射关系
                    print(f"Excel文档转换成功: {filename} -> {name}.pdf")
                    logger.info(f"Excel文档转换成功: {filename} -> {name}.pdf")
                except Exception as e:
                    error_msg = f"Excel文档转换失败 {filename}: {str(e)}"
                    print(error_msg)
                    logger.error(error_msg)
                    # 转换失败时跳过该文件
                    continue

            elif ext_lower in ['.rtf']:
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"RTF文档文件不存在或为空: {filename}")
                    
                    output_pdf_path = os.path.join(output_dir, f"{name}.pdf")
                    rtf_to_pdf(file_path, output_pdf_path)
                    
                    # 检查转换结果
                    if not os.path.exists(output_pdf_path) or os.path.getsize(output_pdf_path) == 0:
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

            elif ext_lower in ['.pdf', '.jpg', '.jpeg', '.png']:
                # 直接复制PDF和图片文件
                try:
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        raise ValueError(f"文件不存在或为空: {filename}")
                    
                    dest_path = os.path.join(output_dir, filename)
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

    def _on_worker_finished(self, filename_str, data, success, error_msg):
        """处理工作线程完成事件"""
        self._cleanup_worker()

        if success:
            self._handle_extraction_success(filename_str, data)
        else:
            self._handle_extraction_error(error_msg)

        if not self.current_workers:
            self._finish_processing()

    def _cleanup_worker(self):
        """清理工作线程"""
        sender = self.sender()
        if sender in self.current_workers:
            self.current_workers.remove(sender)
            sender.deleteLater()

    def _finish_processing(self):
        """完成处理"""
        self._set_processing_state(False)
        self.processing_finished.emit()

    def _handle_extraction_success(self, filename_str, data):
        """处理提取成功"""
        try:
            self._merge_and_save_data(filename_str, data)
            self._cleanup_after_success()
            print(f"成功处理 {len(data)} 条记录")
        except Exception as e:
            error_msg = f"保存数据时出错: {str(e)}"
            QMessageBox.critical(self.view, "错误", error_msg)

    def _merge_and_save_data(self, filename_str, data):
        """合并并保存数据"""
        old_data = self.data_manager.current_data or []
        combined_data = data + old_data

        old_name = self.data_manager.file_name or ""
        new_name = f"{filename_str}, {old_name}".strip(", ")

        self.data_manager.set_current_data(combined_data)
        self.data_manager.set_file_name(new_name)

    def _cleanup_after_success(self):
        """成功后的清理工作"""
        # 清理转换文件夹
        converted_dir = os.path.join(os.getcwd(), "converted_files")
        if os.path.exists(converted_dir):
            try:
                shutil.rmtree(converted_dir)
                print("清理转换文件夹成功")
            except Exception as e:
                print(f"清理转换文件夹失败: {str(e)}")

        self.clear_file_list()
        self.view.title.setText("数据审核工具 - 文件上传")
        self.file_processed.emit()

    def _handle_extraction_error(self, error_msg):
        """处理提取错误"""
        self.view.title.setText("数据审核工具 - 文件上传")
        reply = QMessageBox.critical(
            self.view, 
            "分析失败", 
            f"{error_msg}\n\n点击确定重新尝试上传和分析文件。",
            QMessageBox.Ok | QMessageBox.Cancel
        )
        if reply == QMessageBox.Ok:
            # 重新启用所有按钮，允许用户重新操作
            self._reset_button_states()
            # 清理可能存在的转换文件夹
            self._cleanup_conversion_files()

    # ==================== 公共接口 ====================
    def add_uploaded_file(self, file_paths):
        """添加上传的文件到列表（公共接口）"""
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        self._add_files_to_list(file_paths)

    def add_files(self, files):
        """添加文件到界面（公共接口）"""
        self._add_files_to_list(files)

    def show_file_list(self):
        """显示文件列表（公共接口）"""
        self._update_ui_state()

    def hide_file_list(self):
        """隐藏文件列表（公共接口）"""
        self._reset_to_initial_state()

    # ==================== 错误处理辅助方法 ====================
    def _reset_button_states(self):
        """重置按钮状态为可用"""
        try:
            self.view.upload_button.setEnabled(True)
            self.view.analyze_button.setEnabled(True)
            self.view.clear_button.setEnabled(True)
            self.view.upload_frame.setEnabled(True)
        except Exception as e:
            print(f"重置按钮状态失败: {str(e)}")

    def _cleanup_conversion_files(self):
        """清理转换文件夹"""
        converted_dir = os.path.join(os.getcwd(), "converted_files")
        if os.path.exists(converted_dir):
            try:
                shutil.rmtree(converted_dir)
                print("清理转换文件夹成功")
            except Exception as e:
                print(f"清理转换文件夹失败: {str(e)}")
                logger.error(f"清理转换文件夹失败: {str(e)}")

    def _show_processing_error(self, error_msg: str, title: str = "处理错误"):
        """显示处理错误对话框
        
        Args:
            error_msg: 错误消息
            title: 对话框标题
        """
        reply = QMessageBox.critical(
            self.view,
            title,
            f"{error_msg}\n\n是否要重新尝试？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._reset_button_states()
        return reply == QMessageBox.Yes
