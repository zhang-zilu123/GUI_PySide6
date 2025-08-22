"""
上传功能控制器
处理文件上传相关的业务逻辑

"""
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import QObject, Signal

class UploadController(QObject):
    """上传功能控制器"""
    
    # 定义信号：当文件处理完成时发出
    file_processed = Signal(str, dict)  # 参数为文件路径和处理后的数据
    
    def __init__(self, view):
        """初始化上传控制器"""
        super().__init__()
        self.view = view
        self._connect_signals()
        
    def _connect_signals(self):
        """连接视图信号"""
        # 上传区域点击事件
        self.view.upload_frame.mousePressEvent = self._on_upload_area_clicked
        # 上传按钮点击事件
        self.view.upload_button.clicked.connect(self._on_upload_button_clicked)
        
    def _on_upload_area_clicked(self, event):
        """处理上传区域点击事件"""
        self._open_file_dialog()
        
    def _on_upload_button_clicked(self):
        """处理上传按钮点击事件"""
        self._open_file_dialog()
        
    def _open_file_dialog(self):
        """打开文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, 
            "选择文件", 
            "", 
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        
        if file_path:
            self._process_file(file_path)
            
    def _process_file(self, file_path):
        """处理上传的文件"""
        try:
            # 验证文件
            if not self._validate_file(file_path):
                self.view.update_upload_info("不支持的文件格式", is_error=True)
                return
                
            # 提取数据
            data = self._extract_data_from_pdf(file_path)
            
            # 更新UI
            self.view.update_upload_info(f"已上传: {os.path.basename(file_path)}")
            
            # 发出文件处理完成信号
            self.file_processed.emit(file_path, data)
            
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            self.view.update_upload_info(error_msg, is_error=True)
            QMessageBox.critical(self.view, "错误", error_msg)
            
    def _validate_file(self, file_path):
        """验证文件格式是否支持"""
        if not os.path.isfile(file_path):
            return False
            
        _, ext = os.path.splitext(file_path)
        return ext.lower() == '.pdf'
        
    def _extract_data_from_pdf(self, file_path):
        """从PDF文件中提取数据"""
        # 这里应该是实际的PDF解析逻辑
        # 返回提取的数据
        filename = os.path.basename(file_path)
        return {
            "filename": filename,
            "title": "示例文档",
            "pages": 10,
            "content": ["示例段落1", "示例段落2"],
            "data": [{"id": i+1, "name": f"数据 {i+1}", "value": f"值 {i+1}"} for i in range(5)]
        }