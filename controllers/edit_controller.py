"""
编辑功能控制器
处理数据编辑相关的业务逻辑
"""

import json
import os
from typing import List, Dict, Any, Optional

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QMenu,
    QAbstractItemView,
    QMessageBox,
    QInputDialog,
)

from config.config import EXTRA_FIELD
from utils.common import generate_light_colors


class EditController(QObject):
    """编辑功能控制器

    负责处理数据编辑界面的所有交互逻辑，包括：
    - 数据展示和颜色映射
    - 表格编辑功能
    - 行增删操作
    - 数据保存和同步
    """

    # 定义信号：当数据保存完成时发出
    data_saved = Signal()
    submit_final = Signal()

    def __init__(self, view, data_manager):
        """初始化编辑控制器

        Args:
            view: 编辑视图对象
            data_manager: 数据管理器
        """
        super().__init__()
        self.view = view
        self.data_manager = data_manager
        self.view._controller = self
        self.data: Optional[List[Dict[str, Any]]] = None
        self.current_data: Optional[List[Dict[str, Any]]] = None
        self._connect_signals()

    def _connect_signals(self) -> None:
        """连接视图信号"""
        self.view.finish_button.clicked.connect(self._on_finish_clicked)
        self.view.temp_save_button.clicked.connect(self._on_temp_save_clicked)
        self.view.data_table.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )
        self.view.data_table.cellClicked.connect(self._on_cell_clicked)
        # 设置表格支持多选
        self.view.data_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.data_table.setSelectionBehavior(QAbstractItemView.SelectItems)

    def update_filename(self, filename_str: str) -> None:
        """更新文件名显示

        Args:
            filename_str: 文件名字符串
        """
        self.view.filename_label.setText(f"文件名: {filename_str}")

    def data_display(self, data: List[Dict[str, Any]]) -> None:
        """界面中的数据展示

        Args:
            data: 要显示的数据列表
        """
        data_list = self.data_manager.current_data
        if not data_list:
            return

        self.current_data = data_list.copy()  # 保存当前数据的副本

        # 设置表格行数和列数
        self.view.data_table.setRowCount(len(data_list))
        self.view.data_table.setColumnCount(len(EXTRA_FIELD))
        self.view.data_table.setHorizontalHeaderLabels(EXTRA_FIELD)

        # 使表格可编辑
        self.view.data_table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )

        # 为不同的外销合同分配颜色
        contract_colors = self._generate_contract_colors(data_list)

        # 按照EXTRA_FIELD中的顺序填充表格数据
        self._populate_table_data(data_list, contract_colors)

    def _populate_table_data(
            self, data_list: List[Dict[str, Any]], contract_colors: Dict[tuple, str]
    ) -> None:
        """填充表格数据

        Args:
            data_list: 数据列表
            contract_colors: 合同颜色映射
        """
        for row, data_row in enumerate(data_list):
            contract_value = data_row.get("外销合同", "")
            currency_value = data_row.get("货币代码", "")
            key = (contract_value, currency_value)
            background_color = contract_colors.get(key, "#ffffff")

            for col, field in enumerate(EXTRA_FIELD):
                # 字段值
                value = str(
                    data_row.get(field, "")
                )  # 获取对应值，如果不存在则为空字符串
                value_item = QTableWidgetItem(value)
                value_item.setFlags(
                    value_item.flags() | Qt.ItemIsEditable
                )  # 设置为可编辑

                # 设置背景颜色
                value_item.setBackground(QColor(background_color))

                # 源文件列特殊样式
                if field == "源文件":
                    self._style_source_file_cell(value_item)

                self.view.data_table.setItem(row, col, value_item)

    def _style_source_file_cell(self, item: QTableWidgetItem) -> None:
        """设置源文件单元格样式

        Args:
            item: 表格项
        """
        font = QFont()
        font.setUnderline(True)
        item.setFont(font)
        item.setForeground(Qt.blue)

    def _generate_contract_colors(
            self, data_list: List[Dict[str, Any]]
    ) -> Dict[tuple, str]:
        """为不同的外销合同+货币代码组合生成颜色映射

        Args:
            data_list: 数据列表

        Returns:
            合同颜色映射字典
        """
        # 获取所有唯一的 (外销合同, 货币代码) 组合
        contract_currency_pairs = set()
        for data_row in data_list:
            contract = data_row.get("外销合同", "")
            currency = data_row.get("货币代码", "")
            key = (contract, currency)
            contract_currency_pairs.add(key)

        colors = generate_light_colors()
        # 为每个 (外销合同, 货币代码) 组合分配颜色
        contract_colors = {}
        pair_list = sorted(list(contract_currency_pairs))  # 排序确保一致性

        for i, (contract, currency) in enumerate(pair_list):
            if contract == "" and currency == "":
                contract_colors[(contract, currency)] = "#ffffff"
            else:
                contract_colors[(contract, currency)] = colors[i % len(colors)]

        return contract_colors

        return contract_colors

    def _on_cell_clicked(self, row: int, column: int) -> None:
        """处理单元格点击事件

        Args:
            row: 行号
            column: 列号
        """
        # 获取列标题
        header_item = self.view.data_table.horizontalHeaderItem(column)
        if not header_item:
            return

        column_name = header_item.text()

        # 检查是否点击了"源文件"列
        if column_name == "源文件":
            self._handle_source_file_click(row, column)

    def _handle_source_file_click(self, row: int, column: int) -> None:
        """处理源文件列点击

        Args:
            row: 行号
            column: 列号
        """
        print(f"点击了源文件列，行: {row}, 列: {column}")

        try:
            # 获取该行的源文件值
            item = self.view.data_table.item(row, column)
            if not item:
                QMessageBox.warning(self.view, "警告", "无法获取源文件信息")
                return

            source_file = item.text().strip()
            if not source_file:
                QMessageBox.warning(self.view, "警告", "源文件路径为空")
                return

            print(f"源文件: {source_file}")

            if os.path.exists(source_file):
                try:
                    os.startfile(source_file)
                except Exception as e:
                    error_msg = f"无法打开文件: {str(e)}\n\n可能原因：\n1. 文件被其他程序占用\n2. 没有安装对应的程序\n3. 文件权限不足"
                    reply = QMessageBox.critical(
                        self.view, 
                        "打开文件失败", 
                        error_msg + "\n\n是否要在文件管理器中显示该文件？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        try:
                            # 在文件管理器中显示文件
                            import subprocess
                            subprocess.run(['explorer', '/select,', os.path.normpath(source_file)])
                        except Exception as explorer_error:
                            QMessageBox.warning(self.view, "错误", f"无法打开文件管理器: {str(explorer_error)}")
            else:
                reply = QMessageBox.warning(
                    self.view, 
                    "文件不存在", 
                    f"文件不存在: {source_file}\n\n文件可能已被移动、删除或重命名。\n\n是否要从记录中移除该文件路径？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    item.setText("")  # 清空源文件路径
                    self._collect_current_data()  # 更新数据
                    QMessageBox.information(self.view, "提示", "已清空该记录的源文件路径")
                    
        except Exception as e:
            QMessageBox.critical(self.view, "错误", f"处理源文件点击时发生错误: {str(e)}")

    def _on_context_menu_requested(self, pos) -> None:
        """处理右键菜单请求

        Args:
            pos: 鼠标位置
        """
        item = self.view.data_table.itemAt(pos)
        if not item:
            return

        row = item.row()
        menu = QMenu(self.view)

        # 获取当前选中的项
        selected_items = self.view.data_table.selectedItems()

        if len(selected_items) > 1:
            # 如果选中了多个单元格，添加批量操作选项
            batch_edit_action = menu.addAction(
                f"批量修改所选单元格 ({len(selected_items)}个)"
            )
            batch_clear_action = menu.addAction("清空所选单元格")
            batch_edit_action.triggered.connect(self._batch_edit_cells)
            batch_clear_action.triggered.connect(self._batch_clear_cells)
            menu.addSeparator()

        # 原有的行操作
        delete_action = menu.addAction("删除此行")
        add_action = menu.addAction("在下方增加一行")
        delete_action.triggered.connect(lambda: self.delete_row(row))
        add_action.triggered.connect(lambda: self.add_row(row))

        menu.exec(self.view.data_table.mapToGlobal(pos))

    def _batch_edit_cells(self) -> None:
        """批量编辑选中的单元格"""
        try:
            selected_items = self.view.data_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self.view, "警告", "请先选择要编辑的单元格")
                return

            # 弹出输入对话框
            text, ok = QInputDialog.getText(
                self.view,
                '批量修改',
                f'请输入要设置的值（将应用到{len(selected_items)}个单元格）:'
            )

            if ok and text is not None:
                try:
                    # 批量设置值
                    for item in selected_items:
                        if item:
                            item.setText(text)

                    # 更新数据
                    self._collect_current_data()
                    QMessageBox.information(self.view, '提示', f'已批量修改{len(selected_items)}个单元格')
                except Exception as e:
                    QMessageBox.critical(self.view, "错误", f"批量修改失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self.view, "错误", f"批量编辑操作失败: {str(e)}")

    def _batch_clear_cells(self) -> None:
        """批量清空选中的单元格"""
        selected_items = self.view.data_table.selectedItems()
        if not selected_items:
            return

        # 确认操作
        reply = QMessageBox.question(
            self.view,
            '确认操作',
            f'确定要清空{len(selected_items)}个单元格的内容吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 批量清空
            for item in selected_items:
                item.setText("")

            # 更新数据
            self._collect_current_data()
            QMessageBox.information(self.view, '提示', f'已清空{len(selected_items)}个单元格')

    def _batch_fill_down(self) -> None:
        """批量向下填充（从第一个选中单元格的值填充到其他选中单元格）"""
        selected_items = self.view.data_table.selectedItems()
        if len(selected_items) < 2:
            QMessageBox.warning(self.view, '警告', '请至少选择2个单元格进行向下填充')
            return

        # 找到最上面的单元格作为源值
        source_item = min(selected_items, key=lambda item: (item.row(), item.column()))
        source_value = source_item.text()

        # 确认操作
        reply = QMessageBox.question(
            self.view,
            '确认操作',
            f'确定要将"{source_value}"填充到{len(selected_items) - 1}个单元格吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 批量填充
            for item in selected_items:
                if item != source_item:
                    item.setText(source_value)

            # 更新数据
            self._collect_current_data()
            QMessageBox.information(self.view, '提示', f'已向下填充{len(selected_items) - 1}个单元格')

    def delete_row(self, row: int) -> None:
        """删除指定行

        Args:
            row: 要删除的行号
        """
        self.view.data_table.removeRow(row)
        self._collect_current_data()

    def add_row(self, row: int) -> None:
        """在指定行下方增加一行

        Args:
            row: 基准行号
        """
        new_row = row + 1
        self.view.data_table.insertRow(new_row)
        col_count = self.view.data_table.columnCount()
        custom_color = QColor("#FFF9C4")

        for col in range(col_count):
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setBackground(custom_color)
            self.view.data_table.setItem(new_row, col, item)

        self._collect_current_data()

    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """设置要编辑的数据

        Args:
            data: 要设置的数据
        """
        self.data = data
        # 更新编辑视图中的数据展示
        self.data_display(data)

    def _on_finish_clicked(self) -> None:
        """处理完成按钮点击事件"""
        # 收集当前数据并发出保存信号
        self._collect_current_data()
        self.data_manager.set_current_data(self.data)
        self.submit_final.emit()

    def _on_temp_save_clicked(self) -> None:
        """处理临时保存按钮点击事件"""
        # 收集当前界面的数据
        self._collect_current_data()

        if not self._save_temp_data():
            return

        QMessageBox.information(self.view, "提示", "数据已保存")
        # 发出数据保存完成信号
        self.data_manager.set_current_data(self.data)
        self.data_saved.emit()

    def _save_temp_data(self) -> bool:
        """保存临时数据到文件

        Returns:
            保存是否成功
        """
        try:
            if not self.data:
                QMessageBox.warning(self.view, "警告", "没有数据需要保存")
                return False
                
            temp_dir = "temp"
            if not os.path.exists(temp_dir):
                try:
                    os.makedirs(temp_dir)
                except OSError as e:
                    QMessageBox.critical(self.view, "错误", f"创建临时目录失败: {str(e)}")
                    return False
                    
            temp_path = os.path.join(temp_dir, "temp_data.json")

            # 检查磁盘空间
            try:
                import shutil
                free_space = shutil.disk_usage(temp_dir).free
                if free_space < 1024 * 1024:  # 小于1MB
                    QMessageBox.warning(self.view, "警告", "磁盘空间不足，无法保存数据")
                    return False
            except Exception:
                pass  # 如果检查失败，继续尝试保存

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
                
            # 验证文件是否正确保存
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                QMessageBox.critical(self.view, "错误", "数据保存失败，文件为空或未创建")
                return False
                
            return True
        except PermissionError:
            QMessageBox.critical(self.view, "错误", "没有权限保存到该位置，请检查文件夹权限")
            return False
        except OSError as e:
            QMessageBox.critical(self.view, "错误", f"保存文件时发生系统错误: {str(e)}")
            return False
        except json.JSONEncodeError as e:
            QMessageBox.critical(self.view, "错误", f"数据格式化失败: {str(e)}")
            return False
        except Exception as e:
            QMessageBox.critical(self.view, "错误", f"保存数据失败: {str(e)}")
            return False

    def _collect_current_data(self) -> None:
        """收集当前界面的数据"""
        try:
            if not hasattr(self.view, "data_table") or not self.view.data_table:
                QMessageBox.warning(self.view, "错误", "数据表格未初始化")
                return

            data_list = []
            row_count = self.view.data_table.rowCount()
            col_count = self.view.data_table.columnCount()

            if row_count == 0:
                self.data = []
                return

            for row in range(row_count):
                row_data = {}
                try:
                    for col in range(col_count):
                        # 获取表头标题作为字段名称
                        header_item = self.view.data_table.horizontalHeaderItem(col)
                        if not header_item:
                            continue

                        field_name = header_item.text()

                        # 获取字段值
                        value_item = self.view.data_table.item(row, col)
                        field_value = value_item.text().strip() if value_item else ""

                        # 更新数据
                        row_data[field_name] = field_value
                    
                    if row_data:  # 只添加非空行
                        data_list.append(row_data)
                        
                except Exception as e:
                    print(f"收集第{row}行数据时出错: {str(e)}")
                    continue

            self.data = data_list
            print(f"收集到的数据: {len(self.data)}行")
        except Exception as e:
            QMessageBox.critical(self.view, "错误", f"收集数据时发生错误: {str(e)}")
            self.data = []

    # 可选的编辑模式切换方法（如果需要的话）
    def _on_edit_clicked(self) -> None:
        """处理编辑按钮点击事件"""
        # 使表格可编辑
        self.view.data_table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        # 显示保存按钮
        self.view.temp_save_button.setVisible(True)
        # 更改编辑按钮文本
        self.view.edit_button.setText("结束编辑")
        # 重新连接信号以切换模式
        self.view.edit_button.clicked.disconnect()
        self.view.edit_button.clicked.connect(self._on_end_edit_clicked)

    def _on_end_edit_clicked(self) -> None:
        """处理结束编辑按钮点击事件"""
        # 使表格不可编辑
        self.view.data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 隐藏保存按钮
        self.view.temp_save_button.setVisible(False)
        # 恢复编辑按钮文本
        self.view.edit_button.setText("编辑数据")
        # 重新连接信号
        self.view.edit_button.clicked.disconnect()
        self.view.edit_button.clicked.connect(self._on_edit_clicked)
