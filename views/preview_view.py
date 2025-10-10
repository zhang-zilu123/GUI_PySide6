"""
数据预览界面
用户在此界面确认数据并最终上传
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTextEdit, QApplication,
                             QAbstractItemView)
from PySide6.QtCore import Signal, Qt
from styles import StyleManager
import sys


class PreviewView(QWidget):
    """数据预览界面"""

    def __init__(self):
        """初始化预览界面"""
        super().__init__()

        # 设置界面布局和样式
        self._setup_ui()

    def _setup_ui(self):
        """设置界面UI元素"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)

        # 添加标题
        title = QLabel("数据预览与确认")
        title.setAlignment(Qt.AlignCenter)
        StyleManager.apply_label_style(title, 'title')
        main_layout.addWidget(title)

        # 添加说明文字
        instruction = QLabel("确认以下数据无误后点击上传按钮 或 点击上传文件按钮继续追加数据")
        instruction.setAlignment(Qt.AlignCenter)
        StyleManager.apply_label_style(instruction, 'description')
        main_layout.addWidget(instruction)

        # 创建摘要信息区域
        summary_label = QLabel("数据摘要:")
        StyleManager.apply_label_style(summary_label, 'subtitle')
        main_layout.addWidget(summary_label)

        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(80)
        self.summary_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {StyleManager.get_color('neutral', 300)};
                border-radius: {StyleManager.get_radius('md')};
                background-color: {StyleManager.get_color('neutral', 50)};
                color: {StyleManager.get_color('neutral', 700)};
                font-size: {StyleManager.get_font_size('base')};
                padding: {StyleManager.get_spacing('sm')};
            }}
        """)
        self.summary_text.setReadOnly(True)
        main_layout.addWidget(self.summary_text)

        # 创建数据表格（只读模式）
        self.preview_table = QTableWidget()
        # 设置为整行选择
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置为只读
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                border: 1px solid #ccc;
            }
        """)
        main_layout.addWidget(self.preview_table, 1)  # 表格占据剩余空间

        # 创建按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 添加返回编辑按钮
        self.back_button = QPushButton("返回编辑")
        StyleManager.apply_button_style(self.back_button, 'warning')
        button_layout.addWidget(self.back_button)

        # 添加增加上传文件按钮
        self.upfile_button = QPushButton("继续上传文件")
        self.upfile_button.setVisible(False)
        StyleManager.apply_button_style(self.upfile_button, 'primary')
        button_layout.addWidget(self.upfile_button)

        # 添加弹性空间使上传按钮右对齐
        button_layout.addStretch()

        # 添加登录按钮
        self.load_button = QPushButton("登录")
        StyleManager.apply_button_style(self.load_button, 'secondary')
        button_layout.addWidget(self.load_button)

        # 添加上传按钮
        self.upload_button = QPushButton("提交至OA系统")
        StyleManager.apply_button_style(self.upload_button, 'success')
        button_layout.addWidget(self.upload_button)

        main_layout.addLayout(button_layout)

    def create_table_item(self, text):
        """创建表格项"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item


if __name__ == "__main__":
    """主函数，用于启动应用程序"""
    # 创建QApplication实例
    app = QApplication(sys.argv)

    # 创建预览界面
    preview_view = PreviewView()
    preview_view.setWindowTitle("数据审核工具 - 预览")
    preview_view.resize(800, 600)

    # 显示界面
    preview_view.show()

    # 运行应用程序
    sys.exit(app.exec())
