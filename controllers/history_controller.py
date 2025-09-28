"""
历史记录控制器
处理历史记录相关的业务逻辑
"""
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import QListWidgetItem, QTableWidgetItem
from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QColor

from data.history_manager import HistoryManager
from config.config import HISTORY_FIELD


class HistoryController(QObject):
    """历史记录控制器
    
    负责管理历史记录的显示和操作：
    - 加载历史记录列表
    - 显示记录详情
    - 数据表格更新
    """

    def __init__(self, view, data_manager):
        """初始化历史记录控制器
        
        Args:
            view: 历史记录视图
            data_manager: 数据管理器
        """
        super().__init__()
        self.view = view
        self.data_manager = data_manager
        self.history_manager = HistoryManager()
        self._connect_signals()
        self._load_history()

    def _connect_signals(self) -> None:
        """连接信号"""
        self.view.file_list.itemClicked.connect(self._on_record_selected)

    def _load_history(self) -> None:
        """加载历史记录列表"""
        try:
            self.view.file_list.clear()
            records = self.history_manager.load_upload_records()
            
            if not records:
                # 添加一个提示项
                no_data_item = QListWidgetItem("暂无历史记录")
                no_data_item.setData(Qt.UserRole, None)
                self.view.file_list.addItem(no_data_item)
                return

            for record in records:
                try:
                    self._create_history_item(record)
                except Exception as e:
                    print(f"创建历史记录项失败: {str(e)}")
                    continue
                    
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            error_msg = f"加载历史记录失败: {str(e)}"
            QMessageBox.warning(self.view, "加载失败", error_msg)
            print(error_msg)

    def _create_history_item(self, record: Dict[str, Any]) -> None:
        """创建历史记录项
        
        Args:
            record: 记录数据
        """
        # 创建列表项
        item_text = self._format_item_text(record)
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, record)  # 存储完整记录信息
        self.view.file_list.addItem(item)

    def _format_item_text(self, record: Dict[str, Any]) -> str:
        """格式化列表项文本
        
        Args:
            record: 记录数据
            
        Returns:
            格式化后的文本
        """
        display_time = record.get('display_time', '未知时间')
        filename = record.get('original_filename', '未知文件')
        record_count = record.get('record_count', 0)
        return f"{display_time}\n{filename} ({record_count}条记录)"

    def refresh_history(self) -> None:
        """刷新历史记录列表（供外部调用）"""
        self._load_history()

    def _on_record_selected(self, item: QListWidgetItem) -> None:
        """处理记录选择事件
        
        Args:
            item: 选中的列表项
        """
        try:
            record_info = item.data(Qt.UserRole)
            if not record_info:
                # 可能是"暂无历史记录"项
                self._clear_data_table()
                return

            # 加载详细数据
            record_detail = self._load_record_detail(record_info)
            if not record_detail:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self.view, "加载失败", "无法加载该记录的详细信息，文件可能已被删除或损坏。")
                self._clear_data_table()
                return

            # 更新文件名显示
            self._update_filename_display(record_detail)

            # 更新右侧显示
            self._update_data_table(record_detail)
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            error_msg = f"选择记录时出错: {str(e)}"
            QMessageBox.critical(self.view, "错误", error_msg)
            print(error_msg)

    def _load_record_detail(self, record_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """加载记录详情
        
        Args:
            record_info: 记录信息
            
        Returns:
            记录详情或None
        """
        try:
            file_path = record_info.get('file_path')
            if not file_path:
                print("记录信息中没有文件路径")
                return None
            
            import os
            if not os.path.exists(file_path):
                print(f"历史记录文件不存在: {file_path}")
                return None
                
            return self.history_manager.load_record_detail(file_path)
        except Exception as e:
            print(f"加载记录详情失败: {str(e)}")
            return None

    def _update_filename_display(self, record_detail: Dict[str, Any]) -> None:
        """更新文件名显示
        
        Args:
            record_detail: 记录详情
        """
        if hasattr(self.view, 'file_name_value'):
            filename = record_detail.get('original_filename', '未知文件')
            self.view.file_name_value.setText(filename)

    def _update_data_table(self, record_detail: Dict[str, Any]) -> None:
        """更新数据表格显示
        
        Args:
            record_detail: 记录详情
        """
        try:
            data_list = record_detail.get('data', [])
            
            if not data_list:
                self._clear_data_table()
                return

            # 对数据按 is_error 排序，错误项在前
            sorted_data = self._sort_data_by_error(data_list)

            # 设置表格
            self._setup_table(sorted_data)

            # 填充数据
            self._populate_table_with_data(sorted_data)
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            error_msg = f"更新数据表格失败: {str(e)}"
            QMessageBox.warning(self.view, "显示错误", error_msg)
            print(error_msg)
            self._clear_data_table()

    def _sort_data_by_error(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按错误状态排序数据
        
        Args:
            data_list: 原始数据列表
            
        Returns:
            排序后的数据列表
        """
        return sorted(data_list, key=lambda x: not bool(x.get("is_error", False)))

    def _setup_table(self, data_list: List[Dict[str, Any]]) -> None:
        """设置表格基本属性
        
        Args:
            data_list: 数据列表
        """
        self.view.data_table.setRowCount(len(data_list))
        self.view.data_table.setColumnCount(len(HISTORY_FIELD))
        self.view.data_table.setHorizontalHeaderLabels(HISTORY_FIELD)

    def _populate_table_with_data(self, sorted_data: List[Dict[str, Any]]) -> None:
        """填充表格数据
        
        Args:
            sorted_data: 排序后的数据
        """
        for row, item in enumerate(sorted_data):
            is_error = item.get("is_error", False)

            for col, field in enumerate(HISTORY_FIELD):
                value = self._get_field_value(item, field)
                table_item = QTableWidgetItem(str(value))

                # 如果是错误行，设置红色背景
                if is_error:
                    table_item.setBackground(QColor("#ffebee"))  # 浅红色背景

                self.view.data_table.setItem(row, col, table_item)

    def _get_field_value(self, item: Dict[str, Any], field: str) -> str:
        """获取字段值并进行转换
        
        Args:
            item: 数据项
            field: 字段名
            
        Returns:
            转换后的字段值
        """
        # 字段映射
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

        return value

    def _clear_data_table(self) -> None:
        """清空数据表格"""
        try:
            self.view.data_table.setRowCount(0)
            self.view.data_table.setColumnCount(len(HISTORY_FIELD))
            self.view.data_table.setHorizontalHeaderLabels(HISTORY_FIELD)
            
            # 清空文件名显示
            if hasattr(self.view, 'file_name_value'):
                self.view.file_name_value.setText("请选择历史记录")
        except Exception as e:
            print(f"清空数据表格失败: {str(e)}")

    def refresh_history_safe(self) -> bool:
        """安全地刷新历史记录列表
        
        Returns:
            刷新是否成功
        """
        try:
            self._load_history()
            return True
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            error_msg = f"刷新历史记录失败: {str(e)}"
            QMessageBox.critical(self.view, "刷新失败", error_msg)
            return False
