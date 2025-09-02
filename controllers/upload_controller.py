"""
上传功能控制器
处理文件上传相关的业务逻辑

"""
import os
import shutil
import json
from PySide6.QtWidgets import QFileDialog, QMessageBox, QHBoxLayout, QPushButton
from PySide6.QtCore import QObject, Signal, QThread, Qt

from utils.common import get_filename_list
from utils.mineru_parse import parse_doc
from utils.model_md_to_json import extract_info_from_md
from config.config import EXTRA_FIELD


class ExtractDataWorker(QThread):
    """数据提取工作线程"""
    # 参数为文件名字符串, 提取的数据, 是否成功, 错误信息
    finished = Signal(str, list, bool, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        """在线程中执行耗时操作"""
        filename_list = get_filename_list(self.file_path)
        filename_str = ", ".join(filename_list)
        try:
            # 提取数据
            data = self._extract_data_from_pdf(self.file_path)
            self.finished.emit(filename_str, data, True, "", )
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            self.finished.emit(filename_str, {}, False, error_msg)

    def _extract_data_from_pdf(self, file_path):
        """从PDF文件中提取数据"""
        # 这里应该是实际的PDF解析逻辑
        os.environ['MINERU_MODEL_SOURCE'] = 'local'
        print(f'开始解析PDF文件: {file_path}')
        # 解析pdf
        # local_md_dirs = parse_doc(path_list=file_path, output_dir="./output", backend="pipeline")
        # md_path_list = []
        #
        # for local_md_dir in local_md_dirs:
        #     # 从路径中提取文件名：output和auto之间的部分
        #     path_parts = local_md_dir.replace('\\', '/').split('/')
        #     # 找到output和auto的位置，提取中间的文件名
        #     output_index = path_parts.index('output')
        #     filename = path_parts[output_index + 1]  # output后面的就是文件名
        #
        #     # 构建完整的md文件路径
        #     md_path = os.path.join(local_md_dir, f"{filename}.md")
        #     md_path_list.append(md_path)
        #
        # print('生成的md文件路径:', md_path_list)
        # 大模型解析md文件
        # info_dict = extract_info_from_md(md_path_list)
        info_dict = {
            "费用明细": [
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "海运费",
                    "货币代码": "USD",
                    "金额": "0.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "场站费",
                    "货币代码": "CNY",
                    "金额": "800.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "港杂费",
                    "货币代码": "CNY",
                    "金额": "746.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "单证费",
                    "货币代码": "CNY",
                    "金额": "430.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "THC",
                    "货币代码": "CNY",
                    "金额": "1980.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "舱单费",
                    "货币代码": "CNY",
                    "金额": "150.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "QTS",
                    "货币代码": "CNY",
                    "金额": "1000.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "AFR",
                    "货币代码": "CNY",
                    "金额": "225.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "代理费",
                    "货币代码": "CNY",
                    "金额": "200.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "VGM",
                    "货币代码": "CNY",
                    "金额": "200.00",
                    "备注": ""
                },
                {
                    "外销合同": "DJSCTAO250000746",
                    "船代公司": "青岛林沃供应链管理有限公司",
                    "费用名称": "VGM 411漏收",
                    "货币代码": "CNY",
                    "金额": "100.00",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "仓库内装费",
                    "货币代码": "CNY",
                    "金额": "1998.98",
                    "备注": "横街"
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "仓库燃油附加费",
                    "货币代码": "CNY",
                    "金额": "72.69",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "四五期/大谢附加费(仓库提箱)",
                    "货币代码": "CNY",
                    "金额": "181.73",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "四五期/大谢附加费(仓库重箱)",
                    "货币代码": "CNY",
                    "金额": "254.42",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "提单费",
                    "货币代码": "CNY",
                    "金额": "220.88",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "文件费",
                    "货币代码": "CNY",
                    "金额": "117.80",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "港口堆存费",
                    "货币代码": "CNY",
                    "金额": "36.35",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "港全费",
                    "货币代码": "CNY",
                    "金额": "36.35",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "港口操作费",
                    "货币代码": "CNY",
                    "金额": "1090.35",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "电子装箱单录入费 证操",
                    "货币代码": "CNY",
                    "金额": "10.00",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "综合舱单费",
                    "货币代码": "CNY",
                    "金额": "36.35",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "船公司放箱条形码费",
                    "货币代码": "CNY",
                    "金额": "25.00",
                    "备注": ""
                },
                {
                    "外销合同": "NGBL861447",
                    "船代公司": "美集物流运输(中国)有限公司宁波分公司",
                    "费用名称": "铅封费",
                    "货币代码": "CNY",
                    "金额": "36.35",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "柜仓储",
                    "货币代码": "CNY",
                    "金额": "50.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "电费",
                    "货币代码": "CNY",
                    "金额": "10.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "设备务费",
                    "货币代码": "CNY",
                    "金额": "100.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "设 费",
                    "货币代码": "CNY",
                    "金额": "12.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "Terminal Handling Charge -",
                    "货币代码": "CNY",
                    "金额": "856.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "运",
                    "货币代码": "CNY",
                    "金额": "200.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "费",
                    "货币代码": "CNY",
                    "金额": "400.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "CY Monitoring 费",
                    "货币代码": "CNY",
                    "金额": "34.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "",
                    "货币代码": "CNY",
                    "金额": "450.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "东单签单费 务费",
                    "货币代码": "CNY",
                    "金额": "40.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "订舱费",
                    "货币代码": "CNY",
                    "金额": "144.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "费费",
                    "货币代码": "CNY",
                    "金额": "50.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "验证总传输费",
                    "货币代码": "CNY",
                    "金额": "120.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU03088",
                    "船代公司": "马银宁宁东",
                    "费用名称": "扫费",
                    "货币代码": "CNY",
                    "金额": "5.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU05039",
                    "船代公司": "Century Distribution Systems (Shenzhen) Ltd-Ningbo Branch",
                    "费用名称": "DOCUMENTATION FEE CFS/CFS (FCR)",
                    "货币代码": "CNY",
                    "金额": "580.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU05039",
                    "船代公司": "Century Distribution Systems (Shenzhen) Ltd-Ningbo Branch",
                    "费用名称": "THC PRO-RATE (CBM)",
                    "货币代码": "CNY",
                    "金额": "302.37",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU05039",
                    "船代公司": "Century Distribution Systems (Shenzhen) Ltd-Ningbo Branch",
                    "费用名称": "CUSTOMS CLEARANCE/DECLARATION (EXPORT)",
                    "货币代码": "CNY",
                    "金额": "130.00",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU05039",
                    "船代公司": "Century Distribution Systems (Shenzhen) Ltd-Ningbo Branch",
                    "费用名称": "VGM SUBMISSION/FILING FEE (CBM)",
                    "货币代码": "CNY",
                    "金额": "24.74",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU05039",
                    "船代公司": "Century Distribution Systems (Shenzhen) Ltd-Ningbo Branch",
                    "费用名称": "TRUCKING",
                    "货币代码": "CNY",
                    "金额": "62.43",
                    "备注": ""
                },
                {
                    "外销合同": "G25RU05039",
                    "船代公司": "Century Distribution Systems (Shenzhen) Ltd-Ningbo Branch",
                    "费用名称": "CFS RECEIVING CHARGE (CBM)",
                    "货币代码": "CNY",
                    "金额": "816.90",
                    "备注": ""
                }
            ]
        }
        if isinstance(info_dict, str):
            try:
                info_dict = json.loads(info_dict)
            except json.JSONDecodeError:
                info_dict = {}

        print(f"解析md文件: {info_dict}")
        # if os.path.exists('./output'):
        #     shutil.rmtree('./output')
        #     print('删除临时文件夹 ./output')

        # 构建返回数据
        display_data = []
        if "费用明细" in info_dict and isinstance(info_dict["费用明细"], list):
            # 处理每个费用条目
            for entry_detail in info_dict["费用明细"]:
                entry_info = {field: "" for field in EXTRA_FIELD}

                # 直接从条目中提取各字段
                entry_info["外销合同"] = entry_detail.get("外销合同", "")
                entry_info["船代公司"] = entry_detail.get("船代公司", "")
                entry_info["费用名称"] = entry_detail.get("费用名称", "")
                entry_info["货币代码"] = entry_detail.get("货币代码", "")
                entry_info["金额"] = entry_detail.get("金额", "")
                entry_info["备注"] = entry_detail.get("备注", "")
                display_data.append(entry_info)

            # 🔹 为合同号顺序分配文件路径
        file_index = 0
        contract_to_file = {}

        for entry in display_data:
            contract_no = entry["外销合同"]
            if contract_no not in contract_to_file:  # 第一次遇到这个合同号
                if file_index < len(file_path):
                    contract_to_file[contract_no] = file_path[file_index]
                    file_index += 1
                else:
                    contract_to_file[contract_no] = ""  # 文件不够用，给空
            # 如果只要文件名：os.path.basename(contract_to_file[contract_no])
            entry["源文件"] = contract_to_file[contract_no]

        print(f"返回数据: {display_data}")
        return display_data


class UploadController(QObject):
    """上传功能控制器"""
    # 定义信号：当文件处理完成时发出
    file_processed = Signal(object, str)  # 参数为提取的数据, 文件名字符串
    # 定义信号：当开始处理文件时发出
    processing_started = Signal()
    # 定义信号：当处理完成时发出
    processing_finished = Signal()

    def __init__(self, view):
        """初始化上传控制器"""
        super().__init__()
        self.view = view
        self.uploaded_files = []  # 存储已上传的文件路径
        self.current_workers = []  # 存储当前正在运行的工作线程
        self._connect_signals()

    def _connect_signals(self):
        """连接视图信号"""
        # 上传区域点击事件
        self.view.upload_frame.mousePressEvent = self._on_upload_area_clicked
        # 上传按钮点击事件
        self.view.upload_requested.connect(self._on_upload_requested)
        #  重新上传按钮点击事件
        self.view.clear_requested.connect(self.clear_file_list)
        # 分析按钮点击事件
        self.view.analyze_requested.connect(self._on_analyze_requested)
        # 拖拽文件事件
        self.view.files_dropped.connect(self._on_files_dropped)

    def _on_upload_area_clicked(self, event):
        """处理上传区域点击事件"""
        self._open_file_dialog()

    def _on_upload_requested(self):
        """处理上传请求"""
        self._open_file_dialog()

    def _on_files_dropped(self, file_paths):
        """处理拖拽文件事件"""
        valid_files = []
        for file_path in file_paths:
            if self._validate_file(file_path):  # 验证文件格式
                valid_files.append(file_path)
        if valid_files:
            self.add_uploaded_file(valid_files)

    def _open_file_dialog(self):
        """打开文件选择对话框"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.view,
            "选择文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )

        if file_paths:
            valid_files = []
            for file_path in file_paths:
                if self._validate_file(file_path):  # 验证文件格式
                    valid_files.append(file_path)
            if valid_files:
                self.add_uploaded_file(valid_files)

    def show_file_list(self):
        """显示文件列表，隐藏上传信息框"""
        self.view.upload_frame.setVisible(False)
        self.view.scroll_area.setVisible(True)
        self.view.files_widget.setVisible(True)
        self.view.clear_button.setVisible(True)

    def hide_file_list(self):
        """隐藏文件列表，显示上传信息框"""
        self.view.upload_frame.setVisible(True)
        self.view.scroll_area.setVisible(False)
        self.view.files_widget.setVisible(False)
        self.view.clear_button.setVisible(False)

    def add_files(self, files):
        """添加文件到界面"""
        has_new_files = False
        for file_path in files:
            if file_path not in self.uploaded_files:
                self.uploaded_files.append(file_path)
                has_new_files = True

                # 为每个文件创建一个水平布局，包含文件名按钮和删除按钮
                file_layout = QHBoxLayout()
                file_layout.setContentsMargins(0, 0, 0, 0)

                # 文件名按钮
                file_button = QPushButton(os.path.basename(file_path))
                file_button.setToolTip(file_path)
                file_button.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 8px;
                        border: none;
                        background-color: transparent;
                        border-bottom: 1px solid #eee;
                    }
                    QPushButton:hover {
                        background-color: #f5f5f5;
                    }
                """)
                file_button.setCursor(Qt.PointingHandCursor)

                # 删除按钮
                delete_button = QPushButton("×")
                delete_button.setFixedSize(24, 24)
                delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: #ff4444;
                        color: white;
                        border-radius: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #cc0000;
                    }
                """)
                delete_button.setCursor(Qt.PointingHandCursor)
                delete_button.clicked.connect(lambda checked, fp=file_path: self._remove_file(fp))

                file_layout.addWidget(file_button)
                file_layout.addStretch()
                file_layout.addWidget(delete_button)

                self.view.files_layout.addLayout(file_layout)

        # 如果有新文件添加，显示文件区域和分析按钮
        if has_new_files and len(self.uploaded_files) > 0:
            self.view.scroll_area.setVisible(True)
            self.view.files_widget.setVisible(True)
            self.view.analyze_button.setVisible(True)

        # 如果有新文件添加，显示文件区域和分析按钮
        if has_new_files and len(self.uploaded_files) > 0:
            self.view.scroll_area.setVisible(True)
            self.view.files_widget.setVisible(True)
            self.view.analyze_button.setVisible(True)

    def _remove_file(self, file_path):
        """删除指定文件"""
        if file_path in self.uploaded_files:
            # 从文件路径列表中移除
            self.uploaded_files.remove(file_path)

            # 重新构建文件显示区域
            self._rebuild_file_list()

            # 如果没有文件了，隐藏相关区域
            if len(self.uploaded_files) == 0:
                self.view.scroll_area.setVisible(False)
                self.view.files_widget.setVisible(False)
                self.view.analyze_button.setVisible(False)
                self.view.clear_button.setVisible(False)
                self.view.upload_frame.setVisible(True)
                self.view.upload_button.setVisible(True)
                self.view.upload_button.setText("上传")
                self.view.upload_info.setText("""
                    <div style="font-size: 48px;">📁</div>
                    <div style="font-size: 16px; color: #888;">点击或拖拽文件到此处上传</div>
                    <div style="font-size: 12px; color: #aaa;">支持格式: pdf</div>
                """)
                self.view.instruction.setText("请上传需要审核的数据文件")

    def _rebuild_file_list(self):
        """重新构建文件列表显示"""
        # 清除现有布局中的所有控件
        while self.view.files_layout.count():
            child = self.view.files_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # 递归删除布局中的控件
                sub_layout = child.layout()
                while sub_layout.count():
                    sub_child = sub_layout.takeAt(0)
                    if sub_child.widget():
                        sub_child.widget().deleteLater()

        # 重新添加所有文件
        for file_path in self.uploaded_files:
            # 为每个文件创建一个水平布局，包含文件名按钮和删除按钮
            file_layout = QHBoxLayout()
            file_layout.setContentsMargins(0, 0, 0, 0)

            # 文件名按钮
            file_button = QPushButton(os.path.basename(file_path))
            file_button.setToolTip(file_path)
            file_button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px;
                    border: none;
                    background-color: transparent;
                    border-bottom: 1px solid #eee;
                }
                QPushButton:hover {
                    background-color: #f5f5f5;
                }
            """)
            file_button.setCursor(Qt.PointingHandCursor)

            # 删除按钮
            delete_button = QPushButton("×")
            delete_button.setFixedSize(24, 24)
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff4444;
                    color: white;
                    border-radius: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #cc0000;
                }
            """)
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.clicked.connect(lambda checked, fp=file_path: self._remove_file(fp))

            file_layout.addWidget(file_button)
            file_layout.addStretch()
            file_layout.addWidget(delete_button)

            self.view.files_layout.addLayout(file_layout)

    def add_uploaded_file(self, file_paths):
        """添加上传的文件到列表"""
        # 使用新的文件添加方法
        self.add_files(file_paths)

        # 显示分析按钮
        self.view.analyze_button.setVisible(True)

        # 更新上传按钮文字
        self.view.upload_button.setText("继续上传")

        self.show_file_list()

        self.view.instruction.setText(f"可点击'继续上传'增加需要提取的文件或者点击'开始分析'提取数据")

    def clear_file_list(self):
        """清空文件列表"""
        self.uploaded_files.clear()
        # 清除现有布局中的所有控件
        while self.view.files_layout.count():
            child = self.view.files_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # 递归删除布局中的控件
                sub_layout = child.layout()
                while sub_layout.count():
                    sub_child = sub_layout.takeAt(0)
                    if sub_child.widget():
                        sub_child.widget().deleteLater()

        self.hide_file_list()

        # 隐藏分析按钮
        self.view.analyze_button.setVisible(False)

        # 恢复上传按钮文字
        self.view.upload_button.setText("上传")

        # 重置说明文字
        self.view.instruction.setText("请上传需要审核的数据文件")

    def _on_analyze_requested(self):
        """处理分析请求"""
        if self.uploaded_files:
            # 禁用界面控件
            self._disable_ui_controls()
            # 发出开始处理信号
            self.processing_started.emit()
            self.view.title.setText("正在提取识别中，请稍候...")

            worker = ExtractDataWorker(self.uploaded_files)
            worker.finished.connect(self._on_worker_finished)
            worker.start()
            self.current_workers.append(worker)

    def _disable_ui_controls(self):
        """禁用界面控件"""
        self.view.upload_button.setEnabled(False)
        self.view.analyze_button.setEnabled(False)
        self.view.clear_button.setEnabled(False)
        # 禁用上传区域的点击事件
        self.view.upload_frame.setEnabled(False)

    def _enable_ui_controls(self):
        """启用界面控件"""
        self.view.upload_button.setEnabled(True)
        self.view.analyze_button.setEnabled(True)
        self.view.clear_button.setEnabled(True)
        # 启用上传区域的点击事件
        self.view.upload_frame.setEnabled(True)

    def _on_worker_finished(self, filename_str, data, success, error_msg):
        """处理工作线程完成事件"""
        # 从当前工作线程列表中移除已完成的线程
        sender = self.sender()
        if sender in self.current_workers:
            self.current_workers.remove(sender)

        if success:
            # 发出文件处理完成信号
            self.file_processed.emit(data, filename_str)
        else:
            # 显示错误信息
            QMessageBox.critical(self.view, "错误", error_msg)

        # 如果所有工作线程都完成了，发出处理完成信号
        if not self.current_workers:
            self._enable_ui_controls()
            self.processing_finished.emit()

    def _validate_file(self, file_path):
        """验证文件格式是否支持"""
        if not os.path.isfile(file_path):
            return False

        _, ext = os.path.splitext(file_path)
        return ext.lower() == '.pdf'

    def _process_file(self, file_path):
        """验证上传的文件"""
        try:
            # 验证文件
            if not self._validate_file(file_path):
                # 使用消息框提示错误
                QMessageBox.warning(self.view, "文件格式错误", f"{file_path}不是规定的文件格式，请上传PDF文件")
                return False  # 表示处理失败

            # 文件验证通过，添加到上传列表

            self.add_uploaded_file(file_path)
            return True  # 表示处理成功

        except Exception as e:
            error_msg = f"验证文件时出错: {str(e)}"
            QMessageBox.critical(self.view, "错误", error_msg)
            return False
