"""
编辑功能控制器
处理数据编辑相关的业务逻辑
"""
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QTableWidgetItem
from config.config import EXTRA_FIELD

class EditController(QObject):
    """编辑功能控制器"""
    
    # 定义信号：当数据保存完成时发出
    data_saved = Signal(dict)  # 参数为编辑后的数据
    
    def __init__(self, view):
        """初始化编辑控制器"""
        super().__init__()
        self.view = view
        self.data = None
        self._connect_signals()
        
    def _connect_signals(self):
        """连接视图信号"""
        self.view.finish_button.clicked.connect(self._on_finish_clicked)
        self.view.edit_button.clicked.connect(self._on_edit_clicked)
        self.view.temp_save_button.clicked.connect(self._on_temp_save_clicked)
    
    def data_display(self, data):
        """界面中的数据展示"""
        # 如果传入的是单个字典，转换为列表
        if isinstance(data, dict):
            data_list = [data]
        # 如果传入的是字典列表
        elif isinstance(data, list):
            data_list = data
        else:
            data_list = []
            
        self.current_data = data_list.copy()  # 保存当前数据的副本
        
        # 设置表格行数和列数
        self.view.data_table.setRowCount(len(data_list))
        self.view.data_table.setColumnCount(len(EXTRA_FIELD))
        
        # 设置表格标题
        self.view.data_table.setHorizontalHeaderLabels(EXTRA_FIELD)
        
        # 按照EXTRA_FIELD中的顺序填充表格数据
        for row, data_row in enumerate(data_list):
            for col, field in enumerate(EXTRA_FIELD):
                # 字段值
                value = str(data_row.get(field, ""))  # 获取对应值，如果不存在则为空字符串
                value_item = QTableWidgetItem(value)
                value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)  # 设置为可编辑
                self.view.data_table.setItem(row, col, value_item)


    def set_data(self, data):
        """设置要编辑的数据"""
        self.data = data
        # 更新编辑视图中的数据展示
        self.data_display(data)
        
    def _on_finish_clicked(self):
        """处理完成按钮点击事件"""
        # 收集当前数据并发出保存信号
        self._collect_and_save_data()
        
    def _on_edit_clicked(self):
        """处理编辑按钮点击事件"""
        # 使表格可编辑
        self.view.data_table.setEditTriggers(self.view.data_table.DoubleClicked | self.view.data_table.EditKeyPressed)
        # 显示保存按钮
        self.view.temp_save_button.setVisible(True)
        # 更改编辑按钮文本
        self.view.edit_button.setText("结束编辑")
        # 重新连接信号以切换模式
        self.view.edit_button.clicked.disconnect()
        self.view.edit_button.clicked.connect(self._on_end_edit_clicked)
        
    def _on_end_edit_clicked(self):
        """处理结束编辑按钮点击事件"""
        # 使表格不可编辑
        self.view.data_table.setEditTriggers(self.view.data_table.NoEditTriggers)
        # 隐藏保存按钮
        self.view.temp_save_button.setVisible(False)
        # 恢复编辑按钮文本
        self.view.edit_button.setText("编辑数据")
        # 重新连接信号
        self.view.edit_button.clicked.disconnect()
        self.view.edit_button.clicked.connect(self._on_edit_clicked)
        
    def _on_temp_save_clicked(self):
        """处理临时保存按钮点击事件"""
        # 收集当前编辑的数据并保存
        self._collect_and_save_data()
        
    def _collect_and_save_data(self):
        """收集界面数据并保存"""
        # 收集当前界面的数据
        self._collect_current_data()
        # 发出数据保存完成信号
        self.data_saved.emit(self.data)
        
    def _collect_current_data(self):
        """收集当前界面的数据"""
        # 收集表格数据
        if hasattr(self.view, 'data_table'):
            data_list = []
            for row in range(self.view.data_table.rowCount()):
                row_data = {}
                for col in range(self.view.data_table.columnCount()):
                    # 获取表头标题作为字段名称
                    field_name = self.view.data_table.horizontalHeaderItem(col).text()
                    
                    # 获取字段值
                    value_item = self.view.data_table.item(row, col)
                    field_value = value_item.text() if value_item else ""
                    
                    # 更新数据
                    row_data[field_name] = field_value
                data_list.append(row_data)
            
            self.data = data_list
            print(f"收集到的数据: {self.data}")
    