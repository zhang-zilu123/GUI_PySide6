"""
上传文件界面
用户从此界面选择并上传文件
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QApplication, QFileDialog, QListWidget
from PySide6.QtCore import Signal, Qt
import os
import sys

class UploadView(QWidget):
    """文件上传界面"""
    
    # 定义信号：当用户请求上传文件时发出
    upload_requested = Signal()      # 上传请求信号
    analyze_requested = Signal()      # 分析请求信号
    files_dropped = Signal(list)     # 拖拽文件信号
    clear_requested = Signal()
    
    def __init__(self):
        """初始化上传界面"""
        super().__init__()

        # 设置固定的窗口大小
        self.setFixedSize(700, 600)
        
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
        self.title = QLabel("数据审核工具 - 文件上传")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 30px;")
        layout.addWidget(self.title)
        
        # 添加上传区域说明
        self.instruction = QLabel("请上传需要审核的数据文件")
        self.instruction.setAlignment(Qt.AlignCenter)
        self.instruction.setStyleSheet("font-size: 16px; color: #666; margin-bottom: 20px;")
        layout.addWidget(self.instruction)
        
        # 创建上传区域（带虚线边框的框架）
        self.upload_frame = QFrame()
        self.upload_frame.setFrameStyle(QFrame.Box)
        self.upload_frame.setLineWidth(2)
        self.upload_frame.setStyleSheet("""
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
        self.upload_frame.setMinimumHeight(300)
        
        # 设置上传区域布局
        frame_layout = QVBoxLayout(self.upload_frame)
        frame_layout.setSpacing(15)
        frame_layout.setContentsMargins(20, 20, 20, 20)

        # 创建一个 QLabel 来显示所有文本
        self.upload_info = QLabel(self.upload_frame)
        self.upload_info.setWordWrap(True)  # 允许自动换行
        self.upload_info.setAlignment(Qt.AlignCenter)  # 文本居中
        self.upload_info.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #888;
            }
        """)

        self.upload_info.setText("""
        <div style="font-size: 48px;">📁</div>
        <div style="font-size: 16px; color: #888;">点击或拖拽文件到此处上传</div>
        <div style="font-size: 12px; color: #aaa;">支持格式: pdf</div>
        """)

        # 将 QLabel 添加到布局中
        frame_layout.addWidget(self.upload_info)

        layout.addWidget(self.upload_frame)

        # 添加文件列表显示区域（默认隐藏）
        self.file_list = QListWidget()
        self.file_list.setVisible(False)  # 默认隐藏
        self.file_list.setMaximumHeight(300)
        # 美化文件列表
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fff;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:last-child {
                border-bottom: none;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        layout.addWidget(self.file_list)

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
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                font-weight: 500;
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


        # 添加分析按钮（默认隐藏）
        self.analyze_button = QPushButton("开始分析")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.analyze_button.setCursor(Qt.PointingHandCursor)
        self.analyze_button.setVisible(False)  # 默认隐藏
        layout.addWidget(self.analyze_button)

        # 添加重新上传按钮
        self.clear_button = QPushButton("重新上传")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #EF6C00;
            }
        """)
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.setVisible(False)
        layout.addWidget(self.clear_button)
        
        
        # 连接按钮信号
        self.upload_button.clicked.connect(self._on_upload_button_clicked)
        self.analyze_button.clicked.connect(self._on_analyze_button_clicked)
        self.clear_button.clicked.connect(self._on_clear_button_clicked)
        
        # 启用拖放功能
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """处理拖拽放下事件"""
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
            if files:
                self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()
        
    def _on_upload_button_clicked(self):
        """处理上传按钮点击事件"""
        self.upload_requested.emit()
        
    def _on_analyze_button_clicked(self):
        """处理分析按钮点击事件"""
        self.analyze_requested.emit()
    def _on_clear_button_clicked(self):
        """处理重新上传按钮点击事件"""
        self.clear_requested.emit()
        
    
        

if __name__ == "__main__":
    """主函数，用于启动应用程序"""
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 创建上传界面
    upload_view = UploadView()
    upload_view.setWindowTitle("数据审核工具")
    upload_view.setGeometry(100, 100, 700, 500)
       
    # 显示界面
    upload_view.show()
    
    # 运行应用程序
    sys.exit(app.exec())