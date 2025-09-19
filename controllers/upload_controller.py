"""
上传功能控制器
处理文件上传相关的业务逻辑
"""
import os
import shutil
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import QFileDialog, QMessageBox, QHBoxLayout, QPushButton
from PySide6.QtCore import QObject, Signal, QThread, Qt

from data.temp_data import get_data
from utils.common import get_filename_list
from utils.mineru_parse import parse_doc
from utils.model_md_to_json import extract_info_from_md
from config.config import EXTRA_FIELD, API_KEY
from utils.model_translate import translate_json
from utils.table_corrector_multi import TableCorrector


class ExtractDataWorker(QThread):
    """数据提取工作线程
    
    在后台线程中执行PDF文件解析和数据提取，避免阻塞主线程
    """

    # 信号：参数为文件名字符串, 提取的数据, 是否成功, 错误信息
    finished = Signal(str, list, bool, str)

    def __init__(self, file_paths: List[str]):
        """初始化工作线程
        
        Args:
            file_paths: 要处理的文件路径列表
        """
        super().__init__()
        # 确保 file_paths 是列表
        if isinstance(file_paths, str):
            self.file_paths = [file_paths]
        elif isinstance(file_paths, list):
            self.file_paths = file_paths
        else:
            self.file_paths = list(file_paths)

    def run(self) -> None:
        """在线程中执行耗时操作"""
        try:
            # 获取文件名列表
            filename_list = [os.path.basename(file_path) for file_path in self.file_paths]
            filename_str = ", ".join(filename_list)

            print(f"开始解析PDF文件: {self.file_paths}")
            # 提取数据
            data = self._extract_data_from_pdf(self.file_paths)
            self.finished.emit(filename_str, data, True, "")
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            print(f"Error: {error_msg}")
            self.finished.emit("", [], False, error_msg)

    def _extract_data_from_pdf(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """从PDF文件中提取数据
        
        Args:
            file_paths: PDF文件路径列表
            
        Returns:
            提取的数据列表
        """
        os.environ['MINERU_MODEL_SOURCE'] = 'local'
        print(f'开始解析PDF文件: {file_paths}')

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
        return self._process_extracted_data(info_dict, file_paths)

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
                                file_paths: List[str]) -> List[Dict[str, Any]]:
        """处理提取的数据
        
        Args:
            info_dict: 提取的信息字典
            file_paths: 文件路径列表
            
        Returns:
            处理后的数据列表
        """
        # 建立文件名到完整路径的映射
        file_name_to_path = {}
        for file_path in file_paths:
            file_name = os.path.splitext(os.path.basename(file_path))[0]  # 去掉扩展名
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
            QMessageBox.warning(self.view, "提示", "请先上传文件")
            return

        self._start_analysis()

    def _open_file_dialog(self) -> None:
        """打开文件选择对话框"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.view,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
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
                if not self._is_file_already_uploaded(file_path):
                    valid_files.append(file_path)
                else:
                    self._show_file_exists_message(file_path)
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
        if not os.path.isfile(file_path):
            return False
        _, ext = os.path.splitext(file_path)
        return ext.lower() == '.pdf'

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
        QMessageBox.warning(
            self.view,
            "文件格式错误",
            f"以下文件格式不支持:\n{', '.join(invalid_names)}\n\n请选择PDF文件"
        )

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
        <div style="font-size: 12px; color: #888;">（不建议上传中英混杂的pdf，容易出现解析错误）</div>   
        <div style="font-size: 12px; color: #aaa;">支持格式: pdf</div>
        """)

    def _set_processing_state(self, processing):
        """设置处理状态"""
        enabled = not processing
        self.view.upload_button.setEnabled(enabled)
        self.view.analyze_button.setEnabled(enabled)
        self.view.clear_button.setEnabled(enabled)
        self.view.upload_frame.setEnabled(enabled)

    # ==================== 数据分析处理 ====================
    def _start_analysis(self):
        """开始分析处理"""
        self._set_processing_state(True)
        self.processing_started.emit()
        self.view.title.setText("正在提取识别中，请稍候...")

        worker = ExtractDataWorker(self.uploaded_files.copy())
        worker.finished.connect(self._on_worker_finished)
        worker.start()
        self.current_workers.append(worker)

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
        self.clear_file_list()
        self.view.title.setText("数据审核工具 - 文件上传")
        self.file_processed.emit()

    def _handle_extraction_error(self, error_msg):
        """处理提取错误"""
        self.view.title.setText("数据审核工具 - 文件上传")
        QMessageBox.critical(self.view, "提取失败", error_msg)

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
