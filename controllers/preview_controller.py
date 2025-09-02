"""
预览功能控制器
处理数据预览相关的业务逻辑

(待完善)
"""
import os.path
import shutil

from PySide6.QtCore import QObject, Signal

from config.config import SUBMIT_FIELD


class PreviewController(QObject):
    """预览功能控制器"""

    # 定义信号：当最终上传请求时发出
    final_upload_requested = Signal(list)  # 参数为最终数据
    # 定义信号：当返回编辑请求时发出
    back_to_edit_requested = Signal()
    # 定义信号： 当继续上传请求时发出
    continue_upload_requested = Signal()

    def __init__(self, view):
        """初始化预览控制器"""
        super().__init__()
        self.view = view
        self.data = None
        self._connect_signals()

    def _connect_signals(self):
        """连接视图信号"""
        self.view.back_button.clicked.connect(lambda: self.back_to_edit_requested.emit())
        self.view.upfile_button.clicked.connect(lambda: self.continue_upload_requested.emit())
        self.view.upload_button.clicked.connect(self._on_upload_clicked)

    def set_data(self, data):
        """设置要预览的数据"""
        self.data = data
        self._load_data_to_table()
        self._update_summary()

    def _load_data_to_table(self):
        """加载数据到表格"""
        if not self.data:
            return

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
        summary_text = f"记录数: {data_count}\n状态: 已审核\n准备上传"
        self.view.summary_text.setPlainText(summary_text)

    def _on_upload_clicked(self):
        """处理上传按钮点击事件"""
        if not self.data:
            return
        if os.path.exists('temp'):
            shutil.rmtree('temp')
        # 发出最终上传信号
        self.final_upload_requested.emit(self.data)
