"""
上传功能控制器
处理文件上传相关的业务逻辑
"""

import os
import shutil

from typing import List, Dict
from PySide6.QtWidgets import QFileDialog, QMessageBox, QHBoxLayout, QPushButton
from PySide6.QtCore import QObject, Signal, QThread, Qt

from controllers.extract_data_controller import ExtractDataWorker
from utils.logger import get_upload_logger, get_error_logger
from controllers.file_conversion_controller import DocumentConversionWorker

# 使用统一的日志系统
logger = get_upload_logger()
error_logger = get_error_logger()


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
        self.view.files_pasted.connect(self._on_files_pasted)

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

    def _on_files_pasted(self, file_paths: List[str]) -> None:
        """处理粘贴文件事件

        Args:
            file_paths: 粘贴的文件路径列表
        """
        self._process_selected_files(file_paths)

    def _on_analyze_requested(self) -> None:
        """处理分析请求"""
        if not self.uploaded_files:
            reply = QMessageBox.warning(
                self.view,
                "提示",
                "请先上传文件后再进行分析",
                QMessageBox.Ok | QMessageBox.Cancel,
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
            "支持的文件 (*.pdf *.jpg *.jpeg *.png *.docx *.xls *.xlsx *.rtf);;所有文件 (*.*)",
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

        # 记录总文件数用于提示
        total_count = len(file_paths)

        for file_path in file_paths:
            if self._validate_file(file_path):
                valid_files.append(file_path)
                # if not self._is_file_already_uploaded(file_path):
                #     valid_files.append(file_path)
                # else:
                #     self._show_file_exists_message(file_path)
            else:
                invalid_files.append(file_path)

        self._handle_file_validation_results(valid_files, invalid_files, total_count)

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
                with open(file_path, "rb") as f:
                    # 尝试读取文件头部以确认文件完整性
                    f.read(1024)
            except (IOError, OSError):
                return False

            _, ext = os.path.splitext(file_path)
            valid_extensions = [
                ".pdf",
                ".jpg",
                ".jpeg",
                ".png",
                ".docx",
                ".xls",
                ".xlsx",
                ".rtf",
            ]
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
        if (
            not hasattr(self.data_manager, "uploaded_file_name")
            or not self.data_manager.uploaded_file_name
        ):
            return []
        if isinstance(self.data_manager.uploaded_file_name, str):
            return [
                name.strip() for name in self.data_manager.uploaded_file_name.split(",")
            ]
        return []

    def _get_now_file_names(self) -> List[str]:
        """获取当前文件名列表

        Returns:
            当前文件名列表
        """
        if isinstance(self.data_manager.file_name, str):
            return [name.strip() for name in self.data_manager.file_name.split(",")]
        return []

    def _show_file_exists_message(self, file_path: str) -> None:
        """显示文件已存在的消息

        Args:
            file_path: 文件路径
        """
        file_name = os.path.basename(file_path)
        QMessageBox.information(
            self.view, "文件已存在", f"文件 {file_name} 本次已上传，不能重复上传"
        )

    def _handle_file_validation_results(
        self, valid_files: List[str], invalid_files: List[str], total_count: int = 0
    ) -> None:
        """处理文件验证结果

        Args:
            valid_files: 有效文件列表
            invalid_files: 无效文件列表
            total_count: 总文件数
        """
        if invalid_files:
            self._show_invalid_files_message(
                invalid_files, len(valid_files), total_count
            )
        if valid_files:
            self._add_files_to_list(valid_files)

    def _show_invalid_files_message(
        self, invalid_files: List[str], valid_count: int = 0, total_count: int = 0
    ) -> None:
        """显示无效文件消息

        Args:
            invalid_files: 无效文件列表
            valid_count: 有效文件数量
            total_count: 总文件数
        """
        invalid_names = [os.path.basename(fp) for fp in invalid_files]
        invalid_count = len(invalid_files)

        # 构建消息内容
        message_parts = []

        if total_count > 0:
            message_parts.append(f"共选择了 {total_count} 个文件")

        if valid_count > 0:
            message_parts.append(f"其中 {valid_count} 个文件已成功添加")

        message_parts.append(f"\n以下 {invalid_count} 个文件格式不支持，已自动过滤：")

        # 限制显示的文件名数量，避免消息框过长
        max_display = 10
        if invalid_count <= max_display:
            message_parts.append("\n• " + "\n• ".join(invalid_names))
        else:
            message_parts.append("\n• " + "\n• ".join(invalid_names[:max_display]))
            message_parts.append(f"\n... 还有 {invalid_count - max_display} 个文件")

        message_parts.append("\n\n支持的格式：PDF, JPG, PNG, DOCX, XLS, XLSX, RTF")

        message = "\n".join(message_parts)

        # 如果有有效文件，使用信息提示；否则使用警告提示
        if valid_count > 0:
            QMessageBox.information(self.view, "文件格式提示", message, QMessageBox.Ok)
        else:
            reply = QMessageBox.warning(
                self.view,
                "文件格式错误",
                message + "\n\n点击确定重新选择文件。",
                QMessageBox.Ok | QMessageBox.Cancel,
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
        file_button.setStyleSheet(
            """
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
        """
        )
        file_button.setCursor(Qt.PointingHandCursor)
        return file_button

    def _create_delete_button(self, file_path):
        """创建删除按钮"""
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.setStyleSheet(
            """
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
        """
        )
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
        self.view.upload_info.setText(
            """
            <div style="font-size: 48px;">📁</div>
        <div style="font-size: 16px; color: #888;">点击、拖拽或复制粘贴（Ctrl+V）文件到此处上传</div>
        <div style="font-size: 12px; color: #888;">（不建议上传中英混杂的文件，容易出现解析错误）</div>   
        <div style="font-size: 12px; color: #aaa;">支持格式: pdf、jpg、jpeg、png、docx、xls、xlsx、rtf</div>
        """
        )

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
        document_extensions = [".docx", ".xls", ".xlsx", ".rtf"]
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

        document_extensions = [".docx", ".xls", ".xlsx", ".rtf"]
        pdf_image_extensions = [".pdf", ".jpg", ".jpeg", ".png"]

        for file_path in file_paths:
            _, ext = os.path.splitext(file_path)
            ext_lower = ext.lower()

            if ext_lower in document_extensions:
                document_files.append(file_path)
            elif ext_lower in pdf_image_extensions:
                pdf_image_files.append(file_path)

        return {"documents": document_files, "pdf_images": pdf_image_files}

    # ==================== 数据分析处理 ====================
    def _start_analysis(self):
        """开始分析处理"""
        self._set_processing_state(True)
        self.processing_started.emit()
        self.view.title.setText("正在提取识别中，请稍候...")
        self.view.title.setStyleSheet("color: red; font-weight: bold; font-size: 20px;")

        # 检查是否需要文档转换
        if self._has_document_files(self.uploaded_files):
            # 更新状态提示
            self.view.title.setText("正在转换文件格式，请稍候...")
            self.view.title.setStyleSheet(
                "color: red; font-weight: bold; font-size: 20px;"
            )
            self._start_document_conversion_analysis()
        else:
            self._start_direct_analysis()

    def _start_direct_analysis(self):
        """开始直接分析（原有流程）"""
        worker = ExtractDataWorker(self.uploaded_files.copy())
        worker.finished.connect(self._on_worker_finished)
        worker.status_updated.connect(self._on_status_updated)
        worker.start()
        self.current_workers.append(worker)

    def _start_document_conversion_analysis(self):
        """开始文档转换分析"""
        # 使用项目根目录下的 converted_files 文件夹
        from pathlib import Path

        root_dir = Path(__file__).resolve().parents[1]
        output_dir = str(root_dir / "converted_files")

        # 创建转换工作线程
        conversion_worker = DocumentConversionWorker(self.uploaded_files, output_dir)
        conversion_worker.conversion_finished.connect(self._on_conversion_finished)
        conversion_worker.status_updated.connect(self._on_status_updated)
        conversion_worker.start()
        self.current_workers.append(conversion_worker)

    def _on_conversion_finished(
        self, converted_files, file_mapping, success, error_msg, excel_result=None
    ):
        """处理转换完成事件"""
        self._cleanup_worker()
        if success:
            # 检查是否有 Excel 的特殊处理结果
            if excel_result and excel_result.get("excel_data"):
                # Excel 文件已经完成数据提取
                print(
                    f"Excel 数据提取完成，共 {len(excel_result['excel_data'])} 条记录"
                )
                self._on_status_updated("Excel 数据提取完成...")

                # 直接使用提取的数据
                excel_data = excel_result.get("excel_data", [])
                filename_str = ", ".join(
                    [
                        os.path.basename(f)
                        for f in self.uploaded_files
                        if f.lower().endswith((".xls", ".xlsx"))
                    ]
                )

                # 直接触发完成事件
                self._on_worker_finished(filename_str, excel_data, True, "")
            elif converted_files:
                # 转换成功，开始PDF分析
                print(f"文档转换完成，开始分析 {len(converted_files)} 个文件")
                print(f"文件映射: {file_mapping}")

                output_dir = os.path.dirname(converted_files[0])
                worker = ExtractDataWorker(
                    [output_dir],
                    process_directory=True,
                    original_file_mapping=file_mapping,
                )
                worker.finished.connect(self._on_worker_finished)
                worker.status_updated.connect(self._on_status_updated)
                worker.start()
                self.current_workers.append(worker)
            else:
                error_msg = "转换后未找到有效文件"
                self._handle_extraction_error(error_msg)
        else:
            # 转换失败
            print(f"文档转换失败: {error_msg}")
            self._handle_extraction_error(error_msg)

    def _on_worker_finished(self, filename_str, data, success, error_msg):
        """处理工作线程完成事件"""
        self._cleanup_worker()

        if success:
            self._handle_extraction_success(filename_str, data)
        else:
            self._handle_extraction_error(error_msg)

        if not self.current_workers:
            self._finish_processing()

    def _on_status_updated(self, status_text: str):
        """处理状态更新信号

        Args:
            status_text: 状态文本
        """
        self.view.title.setText(status_text)
        self.view.title.setStyleSheet("color: red; font-weight: bold; font-size: 20px;")

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
            print(f"开始处理提取成功的数据: {len(data)} 条记录")
            # 立即更新UI状态，显示数据处理进度
            self.view.title.setText(f"正在处理数据({len(data)}条记录)，请稍候...")
            self.view.title.setStyleSheet(
                "color: blue; font-weight: bold; font-size: 20px;"
            )
            # 强制刷新UI，防止界面卡顿
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()
            self.processed_files_data = data
            self._merge_and_save_data(filename_str, data)
            self._cleanup_after_success()
            print(f"成功处理 {len(data)} 条记录")
            print(
                f"data_manager 中的数据: {len(self.data_manager.current_data or [])} 条"
            )
            # 立即发射信号，不延迟
            self._emit_data_ready_signal()

        except Exception as e:
            error_msg = f"保存数据时出错: {str(e)}"
            print(f"处理错误: {error_msg}")
            QMessageBox.critical(self.view, "错误", error_msg)
            self._reset_button_states()

    def _emit_data_ready_signal(self):
        """发射数据准备就绪信号"""
        try:
            # 恢复正常标题
            self.view.title.setText("数据审核工具 - 文件上传")
            self.view.title.setStyleSheet("")
            # 确保数据已设置
            if hasattr(self, "processed_files_data") and self.processed_files_data:
                print(
                    f"发射 file_processed 信号，数据量: {len(self.processed_files_data)}"
                )
                self.file_processed.emit()
            else:
                if self.data_manager.current_data:
                    self.processed_files_data = self.data_manager.current_data
                    print(
                        f"从 data_manager 恢复数据: {len(self.processed_files_data)} 条"
                    )
                    self.file_processed.emit()
                else:
                    QMessageBox.warning(
                        self.view, "警告", "数据处理完成，但没有检测到有效数据"
                    )
        except Exception as e:
            print(f"发射数据就绪信号失败: {str(e)}")
            self._reset_button_states()

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
        # 清理转换文件夹 - 使用项目根目录
        from pathlib import Path

        root_dir = Path(__file__).resolve().parents[1]
        converted_dir = root_dir / "converted_files"
        if converted_dir.exists():
            try:
                shutil.rmtree(str(converted_dir))
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
            QMessageBox.Ok | QMessageBox.Cancel,
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
        # 使用项目根目录
        from pathlib import Path

        root_dir = Path(__file__).resolve().parents[1]
        converted_dir = root_dir / "converted_files"
        if converted_dir.exists():
            try:
                shutil.rmtree(str(converted_dir))
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
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._reset_button_states()
        return reply == QMessageBox.Yes
