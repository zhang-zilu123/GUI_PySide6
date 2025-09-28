"""
上传文件界面
用户从此界面选择并上传文件
"""
from PySide6.QtWidgets import (QWidget, QScrollArea, QVBoxLayout, QLabel,
                             QPushButton, QFrame, QApplication, QFileDialog,
                             QListWidget, QHBoxLayout)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from styles import StyleManager
import os
import sys


class UploadView(QWidget):
    """文件上传界面"""
    
    # 定义信号：当用户请求上传文件时发出
    upload_requested = Signal()      # 上传请求信号
    analyze_requested = Signal()     # 分析请求信号
    files_dropped = Signal(list)     # 拖拽文件信号
    clear_requested = Signal()       # 清除请求信号
    
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
        self.title = QLabel("数据审核工具 - 文件上传")
        self.title.setAlignment(Qt.AlignCenter)
        StyleManager.apply_label_style(self.title, 'title')
        layout.addWidget(self.title)
        
        # 添加上传区域说明
        self.instruction = QLabel("请上传需要审核的数据文件")
        self.instruction.setAlignment(Qt.AlignCenter)
        StyleManager.apply_label_style(self.instruction, 'description')
        layout.addWidget(self.instruction)
        
        # 创建上传区域（带虚线边框的框架）
        self.upload_frame = QFrame()
        self.upload_frame.setFrameStyle(QFrame.Box)
        self.upload_frame.setLineWidth(2)
        self.upload_frame.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {StyleManager.get_color('neutral', 300)};
                border-radius: {StyleManager.get_radius('lg')};
                background-color: {StyleManager.get_color('neutral', 50)};
            }}
            QFrame:hover {{
                border-color: {StyleManager.get_color('primary', 400)};
                background-color: {StyleManager.get_color('primary', 50)};
            }}
            QLabel {{
                border: none;
            }}
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
        self.upload_info.setStyleSheet(f"""
            QLabel {{
                font-size: {StyleManager.get_font_size('lg')};
                color: {StyleManager.get_color('neutral', 500)};
            }}
        """)

        self.upload_info.setText("""
        <div style="font-size: 48px;">📁</div>
        <div style="font-size: 16px; color: #64748b;">点击或拖拽文件到此处上传</div>
        <div style="font-size: 12px; color: #94a3b8;">（不建议上传中英混杂的文件，容易出现解析错误）</div>   
        <div style="font-size: 12px; color: #94a3b8;">支持格式: pdf、jpg、jpeg、png、docx、xls、xlsx、rtf</div>
        """)

        # 将 QLabel 添加到布局中
        frame_layout.addWidget(self.upload_info)

        layout.addWidget(self.upload_frame)

        # 创建文件显示区域（默认隐藏）
        self.files_widget = QWidget()
        self.files_layout = QVBoxLayout(self.files_widget)
        self.files_layout.setSpacing(8)
        self.files_layout.setAlignment(Qt.AlignTop)
        self.files_layout.setContentsMargins(10, 10, 10, 10)
        self.files_widget.setVisible(False)
        
        # 创建滚动区域以容纳文件按钮
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.files_widget)
        self.scroll_area.setVisible(False)
        self.scroll_area.setMaximumHeight(200)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fff;
            }
        """)
        layout.addWidget(self.scroll_area)

        # 添加底部按钮区域
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        # 添加上传按钮
        self.upload_button = QPushButton("上传")
        StyleManager.apply_button_style(self.upload_button, 'primary')
        self.upload_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.upload_button)

        # 添加分析按钮（默认隐藏）
        self.analyze_button = QPushButton("开始分析")
        StyleManager.apply_button_style(self.analyze_button, 'success')
        self.analyze_button.setCursor(Qt.PointingHandCursor)
        self.analyze_button.setVisible(False)  # 默认隐藏
        layout.addWidget(self.analyze_button)

        # 添加重新上传按钮
        self.clear_button = QPushButton("重新上传")
        StyleManager.apply_button_style(self.clear_button, 'warning')
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