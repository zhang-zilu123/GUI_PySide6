"""
主窗口类，使用QStackedWidget管理多个界面之间的切换
"""
import json
import os.path

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QStatusBar, QMessageBox
from views.upload_view import UploadView
from views.edit_view import EditView
from views.preview_view import PreviewView
from controllers.upload_controller import UploadController
from controllers.edit_controller import EditController
from controllers.preview_controller import PreviewController


class MainWindow(QMainWindow):
    """应用程序主窗口，负责管理不同界面间的切换"""

    def __init__(self):
        """初始化主窗口"""
        super().__init__()

        # 设置窗口标题和初始大小
        self.setWindowTitle("数据审核工具")
        self.setGeometry(100, 100, 700, 500)
        self.resize(1500, 600)

        # 创建堆叠窗口部件，用于管理多个界面
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 存储所有处理完成的文件数据
        self.processed_files_data = []

        # 初始化界面和控制器
        self._init_ui()

    def _init_ui(self):
        """初始化所有界面并添加到堆叠窗口中"""

        # 创建三个主要界面
        self.upload_view = UploadView()
        self.edit_view = EditView()
        self.preview_view = PreviewView()

        # 创建对应的控制器
        self.upload_controller = UploadController(self.upload_view)
        self.edit_controller = EditController(self.edit_view)
        self.preview_controller = PreviewController(self.preview_view)

        # 将界面添加到堆叠窗口中
        self.stacked_widget.addWidget(self.upload_view)
        self.stacked_widget.addWidget(self.edit_view)
        self.stacked_widget.addWidget(self.preview_view)

        temp_json_path = os.path.join("temp", "temp_data.json")
        if os.path.exists(temp_json_path):
            with open(temp_json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if data:
                        self.preview_controller.set_data(data)
                        self.preview_view.upfile_button.setVisible(True)
                        self.stacked_widget.setCurrentWidget(self.preview_view)
                except json.JSONDecodeError:
                    print("无法解析临时数据文件，可能已损坏。")
                    self.stacked_widget.setCurrentWidget(self.upload_view)
                    QMessageBox.information('提示', '无法解析临时数据文件，可能已损坏。')

        # 连接界面信号
        self._connect_signals()

    def _connect_signals(self):
        """连接各个界面发出的信号"""
        # 上传界面信号
        self.upload_controller.file_processed.connect(self._on_file_processed)
        self.upload_controller.processing_started.connect(self._on_processing_started)
        self.upload_controller.processing_finished.connect(self._on_processing_finished)

        # 编辑界面信号
        self.edit_controller.data_saved.connect(self._on_data_saved)
        self.edit_controller.submit_final.connect(self._on_submit_final)

        # 预览界面信号
        self.preview_controller.final_upload_requested.connect(self._on_final_upload_requested)
        self.preview_controller.back_to_edit_requested.connect(self._on_back_to_edit_requested)
        self.preview_controller.continue_upload_requested.connect(self._on_continue_upload_requested)

    def _on_processing_started(self):
        """处理开始分析事件"""
        self.status_bar.showMessage("正在提取识别中...")

    def _on_processing_finished(self):
        """处理分析完成事件"""
        self.status_bar.showMessage("文件处理完成")
        # 切换到编辑界面并传递所有数据
        self.edit_controller.set_data(self.processed_files_data)
        self.stacked_widget.setCurrentWidget(self.edit_view)
        # 清空已处理的数据列表，为下一次处理做准备
        self.processed_files_data.clear()

    def _on_file_processed(self, data, filename):
        """提取数据完成，传递数据给编辑界面"""
        self.status_bar.showMessage("文件处理完成")
        print('处理完成的文件:', data)
        self.edit_controller.update_filename(filename)
        # 直接保存原始数据，不修改结构
        if isinstance(data, list):
            self.processed_files_data.extend(data)
        elif isinstance(data, dict):
            self.processed_files_data.append(data)
        else:
            print(f"未知的数据格式: {type(data)}")

    def _on_data_saved(self, data):
        """处理数据保存事件"""
        self.status_bar.showMessage("数据已保存")

    def _on_submit_final(self, data):
        """处理最终提交事件"""
        self.status_bar.showMessage("准备上传数据")
        print("最终提交的数据:", data)
        self.preview_controller.set_data(data)
        self.stacked_widget.setCurrentWidget(self.preview_view)

    def _on_final_upload_requested(self, data):
        """处理最终上传请求"""
        self.status_bar.showMessage("数据已上传")
        # 这里可以添加实际的上传逻辑
        print(f"最终上传数据: {data}")
        self.upload_controller.uploaded_files = []
        self.upload_controller.clear_file_list()
        self.upload_view.title.setText("数据审核工具 - 文件上传")
        self.stacked_widget.setCurrentWidget(self.upload_view)

    def _on_back_to_edit_requested(self, data):
        """处理返回编辑请求"""
        self.status_bar.showMessage("返回编辑")
        self.edit_controller.set_data(data)
        # 返回到编辑界面
        self.stacked_widget.setCurrentWidget(self.edit_view)

    def _on_continue_upload_requested(self):
        """处理继续上传请求"""
        self.status_bar.showMessage("继续上传文件")
        # 返回到上传界面
        self.stacked_widget.setCurrentWidget(self.upload_view)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "退出确认",
            "确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
