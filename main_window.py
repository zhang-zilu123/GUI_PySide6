"""
主窗口类，使用QStackedWidget管理多个界面之间的切换
"""

import json
import os.path

from PySide6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QMessageBox,
    QTabWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from controllers.history_controller import HistoryController
from data.data_manager import DataManager
from views.upload_view import UploadView
from views.edit_view import EditView
from views.preview_view import PreviewView
from views.history_view import HistoryView
from controllers.upload_controller import UploadController
from controllers.edit_controller import EditController
from controllers.preview_controller import PreviewController
from styles import StyleManager
from utils.write_to_mineru_json import write_mineru_config


class MainWindow(QMainWindow):
    """应用程序主窗口，负责管理不同界面间的切换"""

    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        write_mineru_config()

        # 初始化数据管理器
        self.data_manager = DataManager()

        # 设置窗口标题和初始大小
        self.setWindowTitle("费用识别工具V4.0")
        self.setGeometry(100, 100, 700, 500)
        self.resize(1500, 600)

        # 应用基础样式
        StyleManager.apply_base_style(self)

        # 创建标签页部件，用于管理多个界面
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)  # 禁止关闭标签页
        self.setCentralWidget(self.tab_widget)

        # 应用标签页样式
        StyleManager.apply_tab_style(self.tab_widget)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        StyleManager.apply_status_bar_style(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 存储所有处理完成的文件数据
        self.processed_files_data = []

        # 初始化界面和控制器
        self._init_ui()

    def _init_ui(self):
        """初始化所有界面并添加到堆叠窗口中"""

        # 创建四个主要界面
        self.upload_view = UploadView()
        self.edit_view = EditView()
        self.preview_view = PreviewView()
        self.history_view = HistoryView()

        # 创建对应的控制器
        self.upload_controller = UploadController(self.upload_view, self.data_manager)
        self.edit_controller = EditController(self.edit_view, self.data_manager)
        self.preview_controller = PreviewController(
            self.preview_view, self.data_manager
        )
        self.history_controller = HistoryController(
            self.history_view, self.data_manager
        )

        # 将界面添加到标签页中
        self.tab_widget.addTab(self.upload_view, "上传文件")
        self.tab_widget.addTab(self.edit_view, "编辑数据")
        self.tab_widget.addTab(self.preview_view, "预览提交")
        self.tab_widget.addTab(self.history_view, "查看历史提交")

        # 连接界面信号
        self._connect_signals()

        # 检查临时数据
        self._check_temp_data()

    def _check_temp_data(self):
        """检查临时数据文件"""
        temp_json_path = os.path.join("temp", "temp_data.json")
        if os.path.exists(temp_json_path):
            with open(temp_json_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if data:
                        source_files = [
                            item.get("源文件", "")
                            for item in data
                            if item.get("源文件")
                        ]
                        unique_source_files = list(set(source_files))
                        filename = [
                            os.path.basename(filepath)
                            for filepath in unique_source_files
                        ]
                        filename_str = ", ".join(filename)
                        self.data_manager.set_file_name(filename_str)
                        self.edit_controller.update_filename(filename_str)
                        self.data_manager.set_current_data(data)
                        self.preview_controller.set_data(data)
                        self.preview_view.upfile_button.setVisible(True)
                        self.edit_controller.set_data(data)
                        self.tab_widget.setCurrentWidget(self.preview_view)

                except json.JSONDecodeError:
                    print("无法解析临时数据文件，可能已损坏。")
                    self.tab_widget.setCurrentWidget(self.upload_view)
                    QMessageBox.information(
                        "提示", "无法解析临时数据文件，可能已损坏。"
                    )

    def _connect_signals(self):
        """连接各个界面发出的信号"""
        # 上传界面信号
        self.upload_controller.file_processed.connect(self._on_file_processed)
        self.upload_controller.processing_started.connect(self._on_processing_started)
        self.upload_controller.processing_finished.connect(self._on_processing_finished)

        # 编辑界面信号
        self.edit_controller.data_saved.connect(
            lambda: self.status_bar.showMessage("数据已保存")
        )
        self.edit_controller.submit_final.connect(self._on_submit_final)

        # 预览界面信号
        self.preview_controller.final_upload_requested.connect(
            self._on_final_upload_requested
        )
        self.preview_controller.back_to_edit_requested.connect(
            self._on_back_to_edit_requested
        )
        self.preview_controller.continue_upload_requested.connect(
            self._on_continue_upload_requested
        )

        # 标签页切换信号
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        """处理标签页切换事件"""
        tab_text = self.tab_widget.tabText(index)
        self.status_bar.showMessage(f"当前页面: {tab_text}")
        # 如果切换到历史记录页面，刷新数据
        if tab_text == "查看历史上传":
            self.history_controller.refresh_history()

    def _on_processing_started(self):
        """处理开始分析事件"""
        self.status_bar.showMessage("正在提取识别中...")

    def _on_processing_finished(self):
        """处理分析完成事件"""
        self.status_bar.showMessage("文件处理完成")
        # 切换到编辑界面并传递所有数据
        self.edit_controller.set_data()
        self.tab_widget.setCurrentWidget(self.edit_view)
        # 清空已处理的数据列表，为下一次处理做准备
        self.processed_files_data.clear()

    def _on_file_processed(self):
        """提取数据完成，传递数据给编辑界面"""
        self.status_bar.showMessage("文件处理完成")
        data = self.data_manager.current_data
        print("处理完成的文件:", data)
        filename = self.data_manager.file_name
        self.edit_controller.update_filename(filename)
        # 直接保存原始数据，不修改结构
        if isinstance(data, list):
            self.processed_files_data.extend(data)
        elif isinstance(data, dict):
            self.processed_files_data.append(data)
        else:
            print(f"未知的数据格式: {type(data)}")

    def _on_submit_final(self):
        """处理最终提交事件"""
        self.status_bar.showMessage("准备上传数据")
        data = self.data_manager.current_data
        print("最终提交的数据:", data)
        self.preview_controller.set_data()
        self.tab_widget.setCurrentWidget(self.preview_view)

    def _on_final_upload_requested(self):
        """处理最终上传请求"""
        self.status_bar.showMessage("数据已上传")
        data = self.data_manager.current_data
        filename = self.data_manager.file_name
        self.data_manager.set_uploaded_file_name(filename)
        self.edit_controller.set_data()
        self.preview_controller.set_data()
        if data:
            self.tab_widget.setCurrentWidget(self.edit_view)
        else:
            self.data_manager.set_file_name("")
            self.edit_controller.update_filename("暂无文件")
            self.tab_widget.setCurrentWidget(self.upload_view)
        # 刷新历史记录
        self.history_controller.refresh_history()

    def _on_back_to_edit_requested(self):
        """处理返回编辑请求"""
        self.status_bar.showMessage("返回编辑")
        self.edit_controller.set_data()
        # 返回到编辑界面
        self.tab_widget.setCurrentWidget(self.edit_view)

    def _on_continue_upload_requested(self):
        """处理继续上传请求"""
        self.status_bar.showMessage("继续上传文件")
        # 返回到上传界面
        self.tab_widget.setCurrentWidget(self.upload_view)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "退出确认",
            "确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
