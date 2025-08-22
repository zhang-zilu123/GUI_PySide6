"""
数据编辑界面
用户在此界面查看和编辑识别后的数据
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QGroupBox, QLineEdit, QApplication)
from PySide6.QtCore import Signal, Qt
import sys

class EditView(QWidget):
    """数据编辑界面"""
    
    # 定义信号：当用户请求保存数据时发出
    save_requested = Signal(dict)  # 参数为编辑后的数据
    
    # 定义信号：当用户请求取消编辑时发出
    cancel_requested = Signal()
    
    def __init__(self):
        """初始化编辑界面"""
        super().__init__()
        
        # 设置界面布局和样式
        self._setup_ui()
        
        # 加载示例数据（这里需要更改，为了能展示gui界面，下面写了一个函数，后续需要更改）
        self._load_sample_data()

    def _load_sample_data(self):
        """加载示例数据"""
        # 设置表格的行列数
        self.data_table.setRowCount(5)
        self.data_table.setColumnCount(4)
        
        # 设置表头
        self.data_table.setHorizontalHeaderLabels(["姓名", "年龄", "职业", "城市"])
        
        # 示例数据
        sample_data = [
            ["张三", "28", "工程师", "北京"],
            ["李四", "32", "设计师", "上海"],
            ["王五", "25", "产品经理", "深圳"],
            ["赵六", "30", "教师", "广州"],
            ["钱七", "27", "医生", "杭州"]
        ]
        
        # 填充数据
        for row, rowData in enumerate(sample_data):
            for col, text in enumerate(rowData):
                self.data_table.setItem(row, col, self.create_table_item(text))
        
    def _setup_ui(self):
        """设置界面UI元素"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)
        
        # 添加标题
        title = QLabel("数据审核与编辑")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        main_layout.addWidget(title)
        
        # 添加说明文字
        instruction = QLabel("请检查并修改识别结果，确认无误后保存")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("color: #666; margin-bottom: 15px;")
        main_layout.addWidget(instruction)
        
        # 创建数据表格
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                border: 1px solid #ccc;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        main_layout.addWidget(self.data_table, 1)  # 表格占据剩余空间
        
       
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

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
        
        # 添加保存按钮
        self.save_button = QPushButton("保存数据")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        button_layout.addWidget(self.save_button)

        # 添加弹性空间使按钮右对齐
        button_layout.addStretch()  
        
        # 添加完成编辑按钮
        self.cancel_button = QPushButton("完成编辑")
        self.cancel_button.setStyleSheet("""
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
        button_layout.addWidget(self.cancel_button)
        
        # 添加弹性空间使按钮右对齐
        # button_layout.addStretch()
        
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
    
    # 创建编辑界面
    edit_view = EditView()
    edit_view.setWindowTitle("数据审核工具 - 编辑")
    edit_view.resize(800, 600)
    
    
    # 显示界面
    edit_view.show()
    
    # 运行应用程序
    sys.exit(app.exec())