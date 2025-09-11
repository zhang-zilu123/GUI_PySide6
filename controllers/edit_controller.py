"""
编辑功能控制器
处理数据编辑相关的业务逻辑
"""
import json
import os
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QColor, QFont, QCursor
from PySide6.QtWidgets import QTableWidgetItem, QMenu, QToolTip, QAbstractItemView
from config.config import EXTRA_FIELD
from PySide6.QtWidgets import QMessageBox

from utils.common import generate_light_colors


class EditController(QObject):
    """编辑功能控制器"""

    # 定义信号：当数据保存完成时发出
    data_saved = Signal()  # 参数为编辑后的数据
    submit_final = Signal()

    def __init__(self, view, data_manager):
        """初始化编辑控制器"""
        super().__init__()
        self.view = view
        self.data_manager = data_manager
        self.view._controller = self
        self.data = None
        self._connect_signals()

    def _connect_signals(self):
        """连接视图信号"""
        self.view.finish_button.clicked.connect(self._on_finish_clicked)
        self.view.temp_save_button.clicked.connect(self._on_temp_save_clicked)
        self.view.data_table.customContextMenuRequested.connect(self._on_context_menu_requested)
        self.view.data_table.cellClicked.connect(self._on_cell_clicked)

    def update_filename(self, filename_str):
        """更新文件名显示"""
        self.view.filename_label.setText(f"文件名: {filename_str}")

    def data_display(self, data):
        """界面中的数据展示"""
        data_list = self.data_manager.current_data
        self.current_data = data_list.copy()  # 保存当前数据的副本

        # 设置表格行数和列数
        self.view.data_table.setRowCount(len(data_list))
        self.view.data_table.setColumnCount(len(EXTRA_FIELD))
        # 设置表格标题
        self.view.data_table.setHorizontalHeaderLabels(EXTRA_FIELD)
        # 使表格可编辑
        self.view.data_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

        # 为不同的外销合同分配颜色
        contract_colors = self._generate_contract_colors(data_list)

        # 按照EXTRA_FIELD中的顺序填充表格数据
        for row, data_row in enumerate(data_list):
            contract_value = data_row.get("外销合同", "")
            currency_value = data_row.get("货币代码", "")
            key = (contract_value, currency_value)
            background_color = contract_colors.get(key, "#ffffff")

            for col, field in enumerate(EXTRA_FIELD):
                # 字段值
                value = str(data_row.get(field, ""))  # 获取对应值，如果不存在则为空字符串
                value_item = QTableWidgetItem(value)
                value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)  # 设置为可编辑

                # 设置背景颜色
                value_item.setBackground(QColor(background_color))
                if field == "源文件":
                    font = QFont()
                    font.setUnderline(True)
                    value_item.setFont(font)
                    value_item.setForeground(Qt.blue)

                self.view.data_table.setItem(row, col, value_item)

    def _generate_contract_colors(self, data_list):
        """为不同的外销合同+货币代码组合生成颜色映射"""
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

    def _on_cell_clicked(self, row, column):
        """处理单元格点击事件"""
        # 获取列标题
        header_item = self.view.data_table.horizontalHeaderItem(column)
        if header_item:
            column_name = header_item.text()

            # 检查是否点击了"源文件"列
            if column_name == "源文件":
                print(f"点击了源文件列，行: {row}, 列: {column}")
                # 获取该行的源文件值
                item = self.view.data_table.item(row, column)
                if item:
                    source_file = item.text()
                    print(f"源文件: {source_file}")
                    if os.path.exists(source_file):
                        os.startfile(source_file)
                    else:
                        print(f"文件不存在: {source_file}")

    def _on_context_menu_requested(self, pos):
        """处理右键菜单请求"""
        item = self.view.data_table.itemAt(pos)
        if item:
            row = item.row()
            menu = QMenu(self.view)
            delete_action = menu.addAction("删除此行")
            add_action = menu.addAction("在下方增加一行")
            delete_action.triggered.connect(lambda: self.delete_row(row))
            add_action.triggered.connect(lambda: self.add_row(row))
            menu.exec(self.view.data_table.mapToGlobal(pos))

    def delete_row(self, row):
        """删除指定行"""
        self.view.data_table.removeRow(row)
        self._collect_current_data()

    def add_row(self, row):
        """在指定行下方增加一行"""
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

    def set_data(self, data):
        """设置要编辑的数据"""
        self.data = data
        # 更新编辑视图中的数据展示
        self.data_display(data)

    def _on_finish_clicked(self):
        """处理完成按钮点击事件"""
        # 收集当前数据并发出保存信号
        self._collect_current_data()
        self.data_manager.set_current_data(self.data)
        self.submit_final.emit()

    def _on_edit_clicked(self):
        """处理编辑按钮点击事件"""
        from PySide6.QtWidgets import QAbstractItemView
        # 使表格可编辑
        self.view.data_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        # 显示保存按钮
        self.view.temp_save_button.setVisible(True)
        # 更改编辑按钮文本
        self.view.edit_button.setText("结束编辑")
        # 重新连接信号以切换模式
        self.view.edit_button.clicked.disconnect()
        self.view.edit_button.clicked.connect(self._on_end_edit_clicked)

    def _on_end_edit_clicked(self):
        """处理结束编辑按钮点击事件"""
        from PySide6.QtWidgets import QAbstractItemView
        # 使表格不可编辑
        self.view.data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 隐藏保存按钮
        self.view.temp_save_button.setVisible(False)
        # 恢复编辑按钮文本
        self.view.edit_button.setText("编辑数据")
        # 重新连接信号
        self.view.edit_button.clicked.disconnect()
        self.view.edit_button.clicked.connect(self._on_edit_clicked)

    def _on_temp_save_clicked(self):
        """处理临时保存按钮点击事件"""
        # 收集当前界面的数据
        self._collect_current_data()
        temp_dir = 'temp'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        temp_path = os.path.join(temp_dir, 'temp_data.json')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self.view, '提示', '数据已保存')
        # 发出数据保存完成信号
        self.data_manager.set_current_data(self.data)
        self.data_saved.emit()

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
