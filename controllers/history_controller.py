from PySide6.QtWidgets import QListWidgetItem, QTableWidgetItem
from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QColor
from data.history_manager import HistoryManager
from config.config import HISTORY_FIELD


class HistoryController(QObject):
    def __init__(self, view, data_manager):
        super().__init__()
        self.view = view
        self.data_manager = data_manager
        self.history_manager = HistoryManager()
        self._connect_signals()
        self._load_history()

    def _connect_signals(self):
        self.view.file_list.itemClicked.connect(self._on_record_selected)

    def _load_history(self):
        """加载历史记录列表"""
        self.view.file_list.clear()
        records = self.history_manager.load_upload_records()

        for record in records:
            # 创建列表项
            item_text = f"{record['display_time']}\n{record['original_filename']} ({record['record_count']}条记录)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, record)  # 存储完整记录信息
            self.view.file_list.addItem(item)

    def refresh_history(self):
        """刷新历史记录列表（供外部调用）"""
        self._load_history()

    def _on_record_selected(self, item):
        """处理记录选择事件"""
        record_info = item.data(Qt.UserRole)
        if not record_info:
            return

        # 加载详细数据
        record_detail = self.history_manager.load_record_detail(record_info['file_path'])
        if not record_detail:
            return

        # 更新文件名显示
        if hasattr(self.view, 'file_name_value'):
            self.view.file_name_value.setText(record_detail.get('original_filename', '未知文件'))

        # 更新右侧显示
        self._update_data_table(record_detail)

    def _update_data_table(self, record_detail):
        """更新数据表格显示"""
        data_list = record_detail.get('data', [])

        # 对数据按 is_error 排序，错误项在前
        sorted_data = sorted(data_list, key=lambda x: not bool(x.get("is_error", False)))

        # 设置表格
        self.view.data_table.setRowCount(len(sorted_data))
        self.view.data_table.setColumnCount(len(HISTORY_FIELD))
        self.view.data_table.setHorizontalHeaderLabels(HISTORY_FIELD)

        # 填充数据
        for row, item in enumerate(sorted_data):
            is_error = item.get("is_error", False)

            for col, field in enumerate(HISTORY_FIELD):
                # 根据字段名映射到数据
                field_mapping = {
                    "外销合同": "外销合同",
                    "船代公司": "船代公司",
                    "费用名称": "费用名称",
                    "货币代码": "货币代码",
                    "金额": "金额",
                    "备注": "备注",
                    "上传情况": "is_error"
                }

                value = item.get(field_mapping.get(field, field), "")

                # 如果是 上传情况 字段，转换布尔值为中文
                if field == "上传情况" and isinstance(value, bool):
                    value = "上传失败" if value else "上传成功"

                table_item = QTableWidgetItem(str(value))

                # 如果是错误行，设置红色背景
                if is_error:
                    table_item.setBackground(QColor("#ffebee"))  # 浅红色背景

                self.view.data_table.setItem(row, col, table_item)
