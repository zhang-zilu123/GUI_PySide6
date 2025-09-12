"""
历史记录界面
用户在此界面查看已上传的文件和历史数据记录
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QTableWidget, QAbstractItemView,
                               QHeaderView, QApplication, QSplitter)
from PySide6.QtCore import Qt
from styles import StyleManager
import sys


class HistoryView(QWidget):
    """历史记录界面"""

    def __init__(self):
        """初始化历史记录界面"""
        super().__init__()

        # 设置界面布局和样式
        self._setup_ui()

    def _setup_ui(self):
        """设置界面UI元素"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)  # 减少间距
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)

        # 添加标题
        title = QLabel("查看历史上传")
        title.setAlignment(Qt.AlignCenter)
        StyleManager.apply_label_style(title, 'title')
        main_layout.addWidget(title)

        # 添加说明文字
        instruction = QLabel("查看已上传的文件和历史数据记录")
        instruction.setAlignment(Qt.AlignCenter)
        StyleManager.apply_label_style(instruction, 'description')
        main_layout.addWidget(instruction)

        # 创建分割器以支持调整大小
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # 左侧区域 - 文件列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)

        # 文件列表标题
        file_list_label = QLabel("上传记录列表")
        StyleManager.apply_label_style(file_list_label, 'subtitle')
        file_list_label.setFixedHeight(25)
        left_layout.addWidget(file_list_label)

        # 文件列表
        self.file_list = QListWidget()
        StyleManager.apply_list_style(self.file_list)
        left_layout.addWidget(self.file_list, 1)  # 让列表占据剩余空间
        splitter.addWidget(left_widget)

        # 右侧区域 - 数据详情
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)

        # 数据详情标题
        data_detail_label = QLabel("数据详情")
        StyleManager.apply_label_style(data_detail_label, 'subtitle')
        data_detail_label.setFixedHeight(25)  # 固定高度
        right_layout.addWidget(data_detail_label)

        # 创建文件名信息区域
        file_info_widget = QWidget()
        file_info_widget.setFixedHeight(40)  # 固定文件信息区域高度
        file_info_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {StyleManager.get_color('neutral', 50)};
                border: 1px solid {StyleManager.get_color('neutral', 200)};
                border-radius: {StyleManager.get_radius('md')};
            }}
        """)
        file_info_layout = QHBoxLayout(file_info_widget)
        file_info_layout.setContentsMargins(10, 8, 10, 8)

        file_name_label = QLabel("文件名:")
        StyleManager.apply_label_style(file_name_label, 'description')

        # 重要：设置可被控制器引用的文件名标签
        self.file_name_value = QLabel("请选择一个记录")
        self.file_name_value.setObjectName("file_name_display")
        StyleManager.apply_label_style(self.file_name_value, 'description')

        file_info_layout.addWidget(file_name_label)
        file_info_layout.addWidget(self.file_name_value)
        file_info_layout.addStretch()

        right_layout.addWidget(file_info_widget)

        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(7)
        # 默认设置为不可编辑
        self.data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 设置表格选择模式
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setAlternatingRowColors(True)

        # 设置表格样式（简洁版本）
        self.data_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                border: 1px solid #ccc;
                background-color: white;
                alternate-background-color: #f8f8f8;
            }
            QTableWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)

        # 设置表格列宽
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # 设置垂直表头样式
        vertical_header = self.data_table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)
        vertical_header.setDefaultSectionSize(30)

        right_layout.addWidget(self.data_table, 1)  # 表格占据剩余空间
        splitter.addWidget(right_widget)

        # 设置分割器的初始比例 (30% : 70%)
        splitter.setSizes([300, 700])


if __name__ == "__main__":
    """主函数，用于启动应用程序"""
    # 创建QApplication实例
    app = QApplication(sys.argv)

    # 创建历史记录界面
    history_view = HistoryView()
    history_view.setWindowTitle("历史记录")
    history_view.setGeometry(100, 100, 900, 650)

    # 显示界面
    history_view.show()

    # 运行应用程序
    sys.exit(app.exec())
