"""
上传文件界面
用户从此界面选择并上传文件
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QApplication, QFileDialog
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
import os
import sys

class UploadView(QWidget):
    """文件上传界面"""
    
    # 定义信号：当用户请求上传文件时发出
    upload_requested = Signal(str)  # 参数为文件路径
    
    def __init__(self):
        """初始化上传界面"""
        super().__init__()
        
        # 设置界面布局和样式
        self._setup_ui()
        
    def _setup_ui(self):
        """设置界面UI元素"""
        # 创建主布局
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        self.setLayout(layout)
        
        # 添加标题
        title = QLabel("数据审核工具 - 文件上传")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 30px;")
        layout.addWidget(title)
        
        # 添加上传区域说明
        instruction = QLabel("请上传需要审核的数据文件")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("font-size: 16px; color: #666; margin-bottom: 20px;")
        layout.addWidget(instruction)
        
        # 创建上传区域（带虚线边框的框架）
        upload_frame = QFrame()
        upload_frame.setFrameStyle(QFrame.Box)
        upload_frame.setLineWidth(2)
        upload_frame.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QFrame:hover {
                border-color: #66b3ff;
                background-color: #f0f8ff;
            }
        """)
        upload_frame.setMinimumHeight(200)
        
        # 设置上传区域布局
        frame_layout = QVBoxLayout(upload_frame)
        frame_layout.setSpacing(15)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加上传图标（使用文本代替实际图标）
        upload_icon = QLabel("📁")
        upload_icon.setAlignment(Qt.AlignCenter)
        upload_icon.setStyleSheet("font-size: 48px;")
        frame_layout.addWidget(upload_icon)
        
        # 添加上传提示文字
        upload_text = QLabel("点击或拖拽文件到此处上传")
        upload_text.setAlignment(Qt.AlignCenter)
        upload_text.setStyleSheet("font-size: 16px; color: #888;")
        frame_layout.addWidget(upload_text)
        
        # 添加支持格式说明
        format_info = QLabel("支持格式: JSON, CSV, Excel")
        format_info.setAlignment(Qt.AlignCenter)
        format_info.setStyleSheet("font-size: 12px; color: #aaa;")
        frame_layout.addWidget(format_info)
        
        layout.addWidget(upload_frame)
        
        # 添加底部按钮区域
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        # 添加上传按钮
        self.upload_button = QPushButton("选择文件并上传")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.upload_button.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.upload_button)
        
        layout.addLayout(button_layout)
        
        # 添加上传区域点击事件
        upload_frame.mousePressEvent = self._on_upload_area_clicked
        
        # 连接按钮点击事件
        self.upload_button.clicked.connect(self._on_upload_button_clicked)
        
        # 启用拖放功能
        self.setAcceptDrops(True)
        
    def _on_upload_area_clicked(self, event):
        """处理上传区域点击事件"""
        self._open_file_dialog()
        
    def _on_upload_button_clicked(self):
        """处理上传按钮点击事件"""
        self._open_file_dialog()
        
    def _open_file_dialog(self):
        """打开文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择文件", 
            "", 
            "支持的文件类型 (*.json *.csv *.xlsx *.xls);;所有文件 (*.*)"
        )
        
        if file_path:
            self.upload_requested.emit(file_path)
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        """处理拖放事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self.upload_requested.emit(file_path)


def main():
    """主函数，用于启动应用程序"""
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 创建上传界面
    upload_view = UploadView()
    upload_view.setWindowTitle("数据审核工具")
    upload_view.resize(600, 500)
    
    # 连接上传信号到处理函数
    upload_view.upload_requested.connect(lambda path: print(f"文件上传请求: {path}"))
    
    # 显示界面
    upload_view.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()