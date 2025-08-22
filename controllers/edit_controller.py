"""
编辑功能控制器
处理数据编辑相关的业务逻辑

(待完善)
"""
from PySide6.QtCore import QObject, Signal

class EditController(QObject):
    """编辑功能控制器"""
    
    # 定义信号：当数据保存时发出
    data_saved = Signal(dict)  # 参数为编辑后的数据
    
    # 定义信号：当编辑取消时发出
    edit_cancelled = Signal()
    
    def __init__(self, view):
        """初始化编辑控制器"""
        super().__init__()
        self.view = view
        self.data = None
        self._connect_signals()
        
    def _connect_signals(self):
        """连接视图信号"""
        self.view.save_button.clicked.connect(self._on_save_clicked)
        self.view.cancel_button.clicked.connect(self._on_cancel_clicked)
        
    def set_data(self, data):
        """设置要编辑的数据"""
        self.data = data
        self._load_data_to_table()
        
    def _load_data_to_table(self):
        """加载数据到表格"""
        if not self.data or "data" not in self.data:
            return
            
        data_list = self.data["data"]
        
        # 设置表格行列数
        self.view.data_table.setRowCount(len(data_list))
        self.view.data_table.setColumnCount(3)  # ID, 名称, 数值
        
        # 设置表头
        headers = ["ID", "名称", "数值"]
        self.view.data_table.setHorizontalHeaderLabels(headers)
        
        # 填充数据
        for row, item in enumerate(data_list):
            self.view.data_table.setItem(row, 0, self.view.create_table_item(str(item.get("id", ""))))
            self.view.data_table.setItem(row, 1, self.view.create_table_item(str(item.get("name", ""))))
            self.view.data_table.setItem(row, 2, self.view.create_table_item(str(item.get("value", ""))))
            
    def _on_save_clicked(self):
        """处理保存按钮点击事件"""
        if not self.data:
            return
            
        # 收集编辑后的数据
        edited_data = self._collect_edited_data()
        
        # 更新数据
        self.data["data"] = edited_data
        
        # 发出数据保存信号
        self.data_saved.emit(self.data)
        
    def _on_cancel_clicked(self):
        """处理取消按钮点击事件"""
        self.edit_cancelled.emit()
        
    def _collect_edited_data(self):
        """收集编辑后的数据"""
        edited_data = []
        row_count = self.view.data_table.rowCount()
        
        for row in range(row_count):
            item_data = {
                "id": self.view.data_table.item(row, 0).text(),
                "name": self.view.data_table.item(row, 1).text(),
                "value": self.view.data_table.item(row, 2).text()
            }
            edited_data.append(item_data)
            
        return edited_data