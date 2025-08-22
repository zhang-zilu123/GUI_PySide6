"""
主窗口类，使用QStackedWidget管理多个界面之间的切换
"""
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QStatusBar
from views.upload_view import UploadView
from views.edit_view import EditView
from views.preview_view import PreviewView

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
        
        # 初始化界面
        self._init_ui()
        
    def _init_ui(self):
        """初始化所有界面并添加到堆叠窗口中"""
        
        # 创建三个主要界面
        self.upload_view = UploadView()
        self.edit_view = EditView()
        self.preview_view = PreviewView()
        
        # 将界面添加到堆叠窗口中
        self.stacked_widget.addWidget(self.upload_view)
        self.stacked_widget.addWidget(self.edit_view)
        self.stacked_widget.addWidget(self.preview_view)
        
        # 设置当前显示的界面（默认显示上传界面）
        self.stacked_widget.setCurrentWidget(self.upload_view)
        
        # 连接界面信号（这里只创建信号连接，不实现具体功能）
        self._connect_signals()
        
    def _connect_signals(self):
        """连接各个界面发出的信号（功能未实现）"""
        # 上传界面信号
        self.upload_view.upload_requested.connect(self._on_upload_requested)
        
        # 编辑界面信号
        self.edit_view.save_requested.connect(self._on_save_requested)
        self.edit_view.cancel_requested.connect(self._on_cancel_editing)
        
        # 预览界面信号
        self.preview_view.final_upload_requested.connect(self._on_final_upload_requested)
        self.preview_view.back_to_edit_requested.connect(self._on_back_to_edit_requested)
        
    def _on_upload_requested(self):
        """处理上传文件请求（功能未实现）"""
        # 此处应实现文件上传逻辑
        self.status_bar.showMessage("文件上传功能未实现")
        
    def _on_save_requested(self, data):
        """处理保存数据请求（功能未实现）"""
        # 此处应实现数据保存逻辑
        self.status_bar.showMessage("数据保存功能未实现")
        
    def _on_cancel_editing(self):
        """处理取消编辑请求（功能未实现）"""
        # 此处应实现取消编辑逻辑
        self.status_bar.showMessage("取消编辑功能未实现")
        
    def _on_final_upload_requested(self, data):
        """处理最终上传请求（功能未实现）"""
        # 此处应实现最终上传逻辑
        self.status_bar.showMessage("最终上传功能未实现")
        
    def _on_back_to_edit_requested(self):
        """处理返回编辑请求（功能未实现）"""
        # 此处应实现返回编辑界面逻辑
        self.status_bar.showMessage("返回编辑功能未实现")