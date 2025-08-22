"""
预览功能控制器
处理数据预览相关的业务逻辑

(待完善)
"""
from PySide6.QtCore import QObject, Signal

class PreviewController(QObject):
    """预览功能控制器"""
    
    # 定义信号：当最终上传请求时发出
    final_upload_requested = Signal(dict)  # 参数为最终数据
    
    # 定义信号：当返回编辑请求时发出
    back_to_edit_requested = Signal()
    
    def __init__(self, view):
        """初始化预览控制器"""
        super().__init__()
        self.view = view
        self.data = None
        self._connect_signals()
        
    def _connect_signals(self):
        """连接视图信号"""
        self.view.back_button.clicked.connect(self._on_back_clicked)
        self.view.upload_button.clicked.connect(self._on_upload_clicked)
        
    def set_data(self, data):
        """设置要预览的数据"""
        self.data = data
        self._load_data_to_table()
        self._update_summary()
        
    def _load_data_to_table(self):
        """加载数据到表格"""
        if not self.data or "data" not in self.data:
            return
            
        data_list = self.data["data"]
        
        # 设置表格行列数
        self.view.preview_table.setRowCount(len(data_list))
        self.view.preview_table.setColumnCount(3)  # ID, 名称, 数值
        
        # 设置表头
        headers = ["ID", "名称", "数值"]
        self.view.preview_table.setHorizontalHeaderLabels(headers)
        
        # 填充数据
        for row, item in enumerate(data_list):
            self.view.preview_table.setItem(row, 0, self.view.create_table_item(str(item.get("id", ""))))
            self.view.preview_table.setItem(row, 1, self.view.create_table_item(str(item.get("name", ""))))
            self.view.preview_table.setItem(row, 2, self.view.create_table_item(str(item.get("value", ""))))
            
    def _update_summary(self):
        """更新摘要信息"""
        if not self.data:
            return
            
        data_count = len(self.data.get("data", []))
        filename = self.data.get("filename", "未知文件")
        
        summary_text = f"文件: {filename}\n记录数: {data_count}\n状态: 已审核\n准备上传"
        self.view.summary_text.setPlainText(summary_text)
        
    def _on_back_clicked(self):
        """处理返回编辑按钮点击事件"""
        self.back_to_edit_requested.emit()
        
    def _on_upload_clicked(self):
        """处理上传按钮点击事件"""
        if not self.data:
            return
            
        # 发出最终上传信号
        self.final_upload_requested.emit(self.data)