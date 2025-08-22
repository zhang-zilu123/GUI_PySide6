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
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 30px;")
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
             QLabel {
                border: none;
            }                     
        """)
        upload_frame.setMinimumHeight(200)
        
        # 设置上传区域布局
        frame_layout = QVBoxLayout(upload_frame)
        frame_layout.setSpacing(15)
        frame_layout.setContentsMargins(20, 20, 20, 20)

        # 创建一个 QLabel 来显示所有文本
        upload_info = QLabel(upload_frame)
        upload_info.setWordWrap(True)  # 允许自动换行
        upload_info.setAlignment(Qt.AlignCenter)  # 文本居中
        upload_info.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #888;
            }
        """)

        upload_info.setText("""
        <div style="font-size: 48px;">📁</div>
        <div style="font-size: 16px; color: #888;">点击或拖拽文件到此处上传</div>
        <div style="font-size: 12px; color: #aaa;">支持格式: pdf</div>
        """)

        # 将 QLabel 添加到布局中
        frame_layout.addWidget(upload_info)
        
        layout.addWidget(upload_frame)
        
        # 添加底部按钮区域
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        # 添加上传按钮
        self.upload_button = QPushButton("上传")
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
        layout.addWidget(self.upload_button)
        
        # 启用拖放功能
        self.setAcceptDrops(True)
        
    def update_upload_info(self, text, is_error=False):
        """更新上传区域显示信息"""
        color = "#d32f2f" if is_error else "#888"
        self.upload_info.setText(f"""
        <div style="font-size: 48px;">📁</div>
        <div style="font-size: 16px; color: {color};">{text}</div>
        <div style="font-size: 12px; color: #aaa;">支持格式: pdf</div>
        """)



if __name__ == "__main__":
    """主函数，用于启动应用程序"""
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 创建上传界面
    upload_view = UploadView()
    upload_view.setWindowTitle("数据审核工具")
    upload_view.resize(600, 500)
       
    # 显示界面
    upload_view.show()
    
    # 运行应用程序
    sys.exit(app.exec())