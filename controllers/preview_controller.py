"""
预览功能控制器
处理数据预览相关的业务逻辑
"""
import os.path
import shutil

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView

from config.config import SUBMIT_FIELD
from data.history_manager import HistoryManager


class LoginDialog(QDialog):
    """登录弹窗，包含WebEngineView用于登录操作"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统登录")
        self.resize(800, 600)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置登录弹窗UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建WebEngineView
        self.web_view = QWebEngineView()
        # 设置默认加载页面，可以根据实际需要修改URL
        self.web_view.load("https://baidu.com")
        
        layout.addWidget(self.web_view)
        self.setLayout(layout)


class PreviewController(QObject):
    """预览功能控制器"""

    # 定义信号：当最终上传请求时发出
    final_upload_requested = Signal()
    # 定义信号：当返回编辑请求时发出
    back_to_edit_requested = Signal()
    # 定义信号： 当继续上传请求时发出
    continue_upload_requested = Signal()


    def __init__(self, view, data_manager):
        """初始化预览控制器"""
        super().__init__()
        self.view = view
        self.data_manager = data_manager
        self.data = None
        self.history_manager = HistoryManager()
        self._connect_signals()

    def _connect_signals(self):
        """连接视图信号"""
        self.view.back_button.clicked.connect(lambda: self.back_to_edit_requested.emit())
        self.view.upfile_button.clicked.connect(lambda: self.continue_upload_requested.emit())
        self.view.upload_button.clicked.connect(self._on_upload_clicked)
        self.view.load_button.clicked.connect(self._on_load_button_clicked)

    def _on_load_button_clicked(self):
        """处理登录按钮点击事件"""
        dialog = LoginDialog(self.view)
        dialog.exec()
        

    def set_data(self, data):
        """设置要预览的数据"""
        self.data = data
        self._load_data_to_table()
        self._update_summary()

    def _load_data_to_table(self):
        """加载数据到表格"""
        data_list = self.data

        # 设置表格行列数
        self.view.preview_table.setRowCount(len(data_list))
        self.view.preview_table.setColumnCount(len(SUBMIT_FIELD))
        # 设置表头
        self.view.preview_table.setHorizontalHeaderLabels(SUBMIT_FIELD)

        # 填充数据
        for row, item in enumerate(data_list):
            self.view.preview_table.setItem(row, 0, self.view.create_table_item(str(item.get("外销合同", ""))))
            self.view.preview_table.setItem(row, 1, self.view.create_table_item(str(item.get("船代公司", ""))))
            self.view.preview_table.setItem(row, 2, self.view.create_table_item(str(item.get("费用名称", ""))))
            self.view.preview_table.setItem(row, 3, self.view.create_table_item(str(item.get("货币代码", ""))))
            self.view.preview_table.setItem(row, 4, self.view.create_table_item(str(item.get("金额", ""))))
            self.view.preview_table.setItem(row, 5, self.view.create_table_item(str(item.get("备注", ""))))

    def _update_summary(self):
        """更新摘要信息"""
        if not self.data:
            self.view.summary_text.setPlainText("暂无数据")
            return

        data_count = len(self.data)
        summary_text = f"记录数: {data_count}\n文件名:{self.data_manager.file_name} \n状态: 已审核\n准备上传"
        self.view.summary_text.setPlainText(summary_text)

    def _on_upload_clicked(self):
        """处理上传按钮点击事件"""
        if not self.data:
            return
        if os.path.exists('temp'):
            shutil.rmtree('temp')
        
        try:
            record_path = self.history_manager.save_upload_record(
                file_name=self.data_manager.file_name,
                data=self.data,
            )
            print(f"上传记录已保存: {record_path}")
        except Exception as e:
            print(f"保存上传记录失败: {e}")
        # 发出最终上传信号
        self.data_manager.set_current_data(self.data)
        self.final_upload_requested.emit()
