"""
数据编辑界面
用户在此界面查看和编辑识别后的数据
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QMenu,
                               QHeaderView, QApplication, QLineEdit, QAbstractItemView)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon
import sys
import os


class EditView(QWidget):
    """数据编辑界面"""

    def __init__(self):
        """初始化编辑界面"""
        super().__init__()

        # 存储当前数据
        self.current_data = {}

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
        self.title_label = QLabel("数据审核与编辑")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; ")
        main_layout.addWidget(self.title_label)

        # 添加说明文字
        instruction = QLabel("请检查并修改识别结果，确认无误后保存")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("color: #666; margin-bottom: 15px;")
        main_layout.addWidget(instruction)

        # 创建文件名显示
        self.filename_label = QLabel('未加载文件')
        self.filename_label.setStyleSheet("color: #333; font-weight: bold;")
        main_layout.addWidget(self.filename_label)

        # 创建数据表格标题
        self.table_label = QLabel("数据表格:")
        self.table_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(self.table_label)

        # 创建表格
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 设置为整行选择
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 默认设置为不可编辑
        self.data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.data_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                border: 1px solid #ccc;
            }
        """)
        main_layout.addWidget(self.data_table, 1)  # 表格占据剩余空间

        # --- 设置表格右键菜单策略 ---
        self.data_table.setContextMenuPolicy(Qt.CustomContextMenu)

        # 创建按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 添加临时保存按钮
        self.temp_save_button = QPushButton("保存")
        self.temp_save_button.setVisible(False)  # 默认隐藏
        self.temp_save_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        button_layout.addWidget(self.temp_save_button)

        # 添加编辑按钮
        self.edit_button = QPushButton("编辑数据")
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #00C957;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00A85A;
            }
        """)
        button_layout.addWidget(self.edit_button)

        # 添加弹性空间使按钮右对齐
        button_layout.addStretch()

        # 添加完成编辑按钮
        self.finish_button = QPushButton("提交")
        self.finish_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(self.finish_button)

        main_layout.addLayout(button_layout)


if __name__ == "__main__":
    """主函数，用于启动应用程序"""
    # 创建QApplication实例
    app = QApplication(sys.argv)

    # 创建编辑界面
    edit_view = EditView()
    edit_view.setWindowTitle("数据审核工具 - 编辑")

    # 显示界面
    edit_view.show()

    # 运行应用程序
    sys.exit(app.exec())
