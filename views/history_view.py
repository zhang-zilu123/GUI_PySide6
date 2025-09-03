"""
历史记录界面
用户在此界面查看已上传的文件和历史数据记录
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QApplication, QSplitter)
from PySide6.QtCore import Qt
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
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)

        # 添加标题
        title = QLabel("查看历史上传")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # 添加说明文字
        instruction = QLabel("查看已上传的文件和历史数据记录")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("color: #666; margin-bottom: 15px;")
        main_layout.addWidget(instruction)

        # 创建分割器以支持调整大小
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)  # 设置分割条宽度
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #ddd;
                border: 1px solid #ccc;
                width: 8px;  /* 明确设置宽度 */
            }
        """)
        main_layout.addWidget(splitter)

        # 左侧区域 - 文件列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 文件列表标题
        file_list_label = QLabel("上传记录ID")
        file_list_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        left_layout.addWidget(file_list_label)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fff;
                min-height: 700px; 
                max-height: 800px; 
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        left_layout.addWidget(self.file_list)
        splitter.addWidget(left_widget)

        # 右侧区域 - 数据详情
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 数据详情标题
        data_detail_label = QLabel("数据详情")
        data_detail_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        right_layout.addWidget(data_detail_label)

        # 创建文件名信息区域（并列显示）
        file_info_widget = QWidget()
        file_info_layout = QHBoxLayout(file_info_widget)
        file_info_layout.setContentsMargins(0, 0, 0, 10)  # 底部留一些间距
        
        file_name_label = QLabel("文件名: ")
        file_name_label.setStyleSheet("font-weight: bold;")
        
        file_name_value = QLabel("aaa.xlsx")
        file_name_value.setStyleSheet("margin-left: 5px;")
        
        file_info_layout.addWidget(file_name_label)
        file_info_layout.addWidget(file_name_value)
        file_info_layout.addStretch()  # 添加弹性空间，使标签靠左对齐
        
        right_layout.addWidget(file_info_widget)

        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
       
        self.data_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fff;
                min-height: 700px; 
                max-height: 800px; 
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        # 设置表格列宽
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # 设置垂直表头样式
        vertical_header = self.data_table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)
        vertical_header.setDefaultSectionSize(25)
        
        right_layout.addWidget(self.data_table)
        splitter.addWidget(right_widget)

        # 设置分割器初始大小和拉伸因子，使两个区域尽可能长
        splitter.setSizes([250, 550])
        splitter.setStretchFactor(0, 1)  # 左侧区域可拉伸
        splitter.setStretchFactor(1, 2)  # 右侧区域更大比例拉伸

        # 设置窗口最小尺寸
        self.setMinimumSize(700, 500)


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