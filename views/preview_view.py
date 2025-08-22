"""
数据预览界面
用户在此界面确认数据并最终上传
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QTextEdit, QApplication)
from PySide6.QtCore import Signal
import sys

class PreviewView(QWidget):
    """数据预览界面"""
    
    # 定义信号：当用户请求最终上传数据时发出
    final_upload_requested = Signal(dict)  # 参数为最终数据
    
    # 定义信号：当用户请求返回编辑时发出
    back_to_edit_requested = Signal()
    
    def __init__(self):
        """初始化预览界面"""
        super().__init__()
        
        # 设置界面布局和样式
        self._setup_ui()
        
        # 加载示例数据（实际应用中应从编辑界面传递）
        self._load_sample_data()
        
    def _setup_ui(self):
        """设置界面UI元素"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)
        
        # 添加标题
        title = QLabel("数据预览与确认")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # 添加说明文字
        instruction = QLabel("请确认以下数据无误后点击上传按钮")
        instruction.setStyleSheet("color: #666; margin-bottom: 15px;")
        main_layout.addWidget(instruction)
        
        # 创建数据表格（只读模式）
        self.preview_table = QTableWidget()
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
        
        # 创建摘要信息区域
        summary_label = QLabel("数据摘要:")
        summary_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        main_layout.addWidget(summary_label)
        
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(80)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                background-color: #f9f9f9;
            }
        """)
        self.summary_text.setReadOnly(True)
        main_layout.addWidget(self.summary_text)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 添加返回编辑按钮
        self.back_button = QPushButton("返回编辑")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
        """)
        button_layout.addWidget(self.back_button)
        
        # 添加弹性空间使上传按钮右对齐
        button_layout.addStretch()
        
        # 添加上传按钮
        self.upload_button = QPushButton("确认上传")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.upload_button)
        
        main_layout.addLayout(button_layout)
        
        # 连接按钮点击事件
        self.back_button.clicked.connect(self._on_back_clicked)
        self.upload_button.clicked.connect(self._on_upload_clicked)
        
    def _load_sample_data(self):
        """加载示例数据到表格"""
        # 设置表格行列数
        self.preview_table.setRowCount(3)
        self.preview_table.setColumnCount(4)
        
        # 设置表头
        headers = ["ID", "名称", "数值", "状态"]
        self.preview_table.setHorizontalHeaderLabels(headers)
        
        # 填充示例数据
        for row in range(3):
            for col in range(4):
                item = QTableWidgetItem(f"预览数据 {row+1}-{col+1}")
                self.preview_table.setItem(row, col, item)
                
        # 设置摘要信息
        self.summary_text.setPlainText("总计: 3条记录\n状态: 已审核\n准备上传")
        
    def _on_back_clicked(self):
        """处理返回编辑按钮点击事件"""
        self.back_to_edit_requested.emit()
        
    def _on_upload_clicked(self):
        """处理上传按钮点击事件"""
        # 收集最终数据（这里使用示例数据）
        final_data = {
            "total_records": 3,
            "status": "已审核",
            "data": [{"id": i+1, "name": f"预览数据 {i+1}-1", "value": f"预览数据 {i+1}-2", "status": f"预览数据 {i+1}-3"} 
                    for i in range(3)]
        }
        self.final_upload_requested.emit(final_data)


def main():
    """主函数，用于启动应用程序"""
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 创建预览界面
    preview_view = PreviewView()
    preview_view.setWindowTitle("数据审核工具 - 预览")
    preview_view.resize(800, 600)
    
    # 连接信号到处理函数
    preview_view.back_to_edit_requested.connect(lambda: print("返回编辑界面"))
    preview_view.final_upload_requested.connect(lambda data: print(f"最终上传数据: {data}"))
    
    # 显示界面
    preview_view.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()