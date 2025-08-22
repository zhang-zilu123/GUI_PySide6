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
        
        # 加载示例数据（实际应用中应从文件或API获取）
        self._load_sample_data()
        
    def _setup_ui(self):
        """设置界面UI元素"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)
        
        # 添加标题
        title = QLabel("数据审核与编辑")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # 添加说明文字
        instruction = QLabel("请检查并修改识别结果，确认无误后保存")
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
        
        # 创建详情编辑区域
        details_group = QGroupBox("详情编辑")
        details_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        details_layout = QVBoxLayout()
        
        # 创建表单布局用于编辑字段
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        # 添加示例字段编辑器
        field1_layout = QHBoxLayout()
        field1_layout.addWidget(QLabel("字段1:"))
        self.field1_edit = QLineEdit()
        field1_layout.addWidget(self.field1_edit)
        form_layout.addLayout(field1_layout)
        
        field2_layout = QHBoxLayout()
        field2_layout.addWidget(QLabel("字段2:"))
        self.field2_edit = QLineEdit()
        field2_layout.addWidget(self.field2_edit)
        form_layout.addLayout(field2_layout)
        
        details_layout.addLayout(form_layout)
        details_group.setLayout(details_layout)
        
        main_layout.addWidget(details_group)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
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
        
        # 添加取消按钮
        self.cancel_button = QPushButton("取消")
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
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 连接按钮点击事件
        self.save_button.clicked.connect(self._on_save_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        
    def _load_sample_data(self):
        """加载示例数据到表格"""
        # 设置表格行列数
        self.data_table.setRowCount(5)
        self.data_table.setColumnCount(4)
        
        # 设置表头
        headers = ["ID", "名称", "数值", "状态"]
        self.data_table.setHorizontalHeaderLabels(headers)
        
        # 填充示例数据
        for row in range(5):
            for col in range(4):
                item = QTableWidgetItem(f"示例数据 {row+1}-{col+1}")
                self.data_table.setItem(row, col, item)
                
        # 连接表格选择变化事件
        self.data_table.itemSelectionChanged.connect(self._on_selection_changed)
        
    def _on_selection_changed(self):
        """处理表格选择变化事件"""
        selected_items = self.data_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            # 更新编辑框中的内容
            self.field1_edit.setText(self.data_table.item(row, 1).text())
            self.field2_edit.setText(self.data_table.item(row, 2).text())
            
    def _on_save_clicked(self):
        """处理保存按钮点击事件"""
        # 收集编辑后的数据
        edited_data = {
            "field1": self.field1_edit.text(),
            "field2": self.field2_edit.text()
        }
        # 发出保存信号
        self.save_requested.emit(edited_data)
        
    def _on_cancel_clicked(self):
        """处理取消按钮点击事件"""
        self.cancel_requested.emit()


def main():
    """主函数，用于启动应用程序"""
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 创建编辑界面
    edit_view = EditView()
    edit_view.setWindowTitle("数据审核工具 - 编辑")
    edit_view.resize(800, 600)
    
    # 连接信号到处理函数
    edit_view.save_requested.connect(lambda data: print(f"保存数据: {data}"))
    edit_view.cancel_requested.connect(lambda: print("取消编辑"))
    
    # 显示界面
    edit_view.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()