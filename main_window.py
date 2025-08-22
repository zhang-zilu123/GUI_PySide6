"""
主窗口类，使用QStackedWidget管理多个界面之间的切换
"""
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QStatusBar
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
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建堆叠窗口部件，用于管理多个界面
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
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
        
        # 设置当前显示的界面（默认显示上传界面）
        self.stacked_widget.setCurrentWidget(self.upload_view)
        
        # 连接界面信号
        self._connect_signals()
        
    def _connect_signals(self):
        """连接各个界面发出的信号"""
        # 上传界面信号
        self.upload_controller.file_processed.connect(self._on_file_processed)
        
        # 编辑界面信号
        self.edit_controller.data_saved.connect(self._on_data_saved)
        self.edit_controller.edit_cancelled.connect(self._on_edit_cancelled)
        
        # 预览界面信号
        self.preview_controller.final_upload_requested.connect(self._on_final_upload_requested)
        self.preview_controller.back_to_edit_requested.connect(self._on_back_to_edit_requested)
        
    def _on_file_processed(self, file_path, data):
        """处理文件处理完成事件"""
        self.status_bar.showMessage(f"文件处理完成: {file_path}")
        # 切换到编辑界面并传递数据
        self.edit_controller.set_data(data)
        self.stacked_widget.setCurrentWidget(self.edit_view)
        
    def _on_data_saved(self, data):
        """处理数据保存事件"""
        self.status_bar.showMessage("数据已保存")
        # 切换到预览界面并传递数据
        self.preview_controller.set_data(data)
        self.stacked_widget.setCurrentWidget(self.preview_view)
        
    def _on_edit_cancelled(self):
        """处理取消编辑事件"""
        self.status_bar.showMessage("编辑已取消")
        # 返回到上传界面
        self.stacked_widget.setCurrentWidget(self.upload_view)
        
    def _on_final_upload_requested(self, data):
        """处理最终上传请求"""
        self.status_bar.showMessage("数据已上传")
        # 这里可以添加实际的上传逻辑
        print(f"最终上传数据: {data}")
        
    def _on_back_to_edit_requested(self):
        """处理返回编辑请求"""
        self.status_bar.showMessage("返回编辑")
        # 返回到编辑界面
        self.stacked_widget.setCurrentWidget(self.edit_view)