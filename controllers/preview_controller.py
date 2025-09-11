"""
预览功能控制器
处理数据预览相关的业务逻辑
"""
import json
import os.path
import shutil
import requests

from PySide6.QtCore import QObject, Signal, Qt, QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QProgressBar, \
    QDialog, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from config.config import SUBMIT_FIELD
from data.history_manager import HistoryManager
from data.token_manager import token_manager


class LoginDialog(QDialog):
    """登录弹窗，包含WebEngineView用于扫码登录操作"""
    login_success = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统登录")
        self.network_manager = QNetworkAccessManager(self)
        self.resize(800, 600)
        self._setup_ui()
        self.get_login_url()

    def _setup_ui(self):
        """初始化UI布局和WebEngineView"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        # 监听页面跳转
        self.web_view.urlChanged.connect(self.on_url_changed)

    def get_login_url(self):
        """请求后端获取扫码登录页面URL"""
        api_url = 'http://47.100.46.227:5586/api/login/qw_login_url?next=/chat'
        request = QNetworkRequest(QUrl(api_url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        request.setRawHeader(b"User-Agent", b"PySide6 Network Client")
        reply = self.network_manager.get(request)
        reply.finished.connect(self.handle_get_url_response)

    def handle_get_url_response(self):
        """处理扫码登录页面URL的响应"""
        reply = self.sender()
        if not isinstance(reply, QNetworkReply):
            return
        if reply.error() == QNetworkReply.NetworkError.NoError:
            try:
                data = json.loads(reply.readAll().data().decode())
                login_url = data.get('data', '') if isinstance(data, dict) else str(data)
                if login_url:
                    self.web_view.load(login_url)
                    self.web_view.setVisible(True)
                else:
                    raise ValueError("无法获取登录URL")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"解析登录URL失败: {e}")
        else:
            QMessageBox.critical(self, "错误", "网络连接失败")
        reply.deleteLater()

    def on_url_changed(self, qurl):
        """监听扫码后页面跳转，获取code和state参数并请求后端登录"""
        url = qurl.toString()
        print("页面跳转到：", url)
        if "/login2" in url:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            code = params.get("code", [""])[0]
            state = params.get("state", [""])[0]
            # 构造登录请求
            api_url = 'http://47.100.46.227:5586/api/login/qw_login'
            request = QNetworkRequest(QUrl(api_url))
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            payload = {
                'code': code,
                'state': state
            }
            json_data = json.dumps(payload).encode('utf-8')
            reply = self.network_manager.post(request, json_data)
            reply.finished.connect(self.handle_login_response)

    def handle_login_response(self):
        """处理扫码登录后的后端响应，保存token并关闭弹窗"""
        reply = self.sender()
        if not isinstance(reply, QNetworkReply):
            return
        if reply.error() == QNetworkReply.NetworkError.NoError:
            try:
                data = json.loads(reply.readAll().data().decode())
                if data.get('code') == 200:
                    self.web_view.urlChanged.disconnect(self.on_url_changed)
                    token = data.get('data', {}).get('token', '')
                    token_manager.set_token(token)
                    self.login_success.emit()
                    QMessageBox.information(self, "成功", "登录成功, 可上传数据")
                    self.accept()
                else:
                    raise ValueError(data.get('message', '登录失败'))
            except Exception as e:
                QMessageBox.warning(self, "错误", f"登录响应解析失败: {e}")
        else:
            QMessageBox.critical(self, "错误", "网络连接失败")
        reply.deleteLater()


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
        self.dialog = LoginDialog(self.view)
        self.dialog.login_success.connect(self._on_login_success)
        self.dialog.show()

    def _on_login_success(self):
        token = token_manager.token
        if token:
            self.view.load_button.setVisible(False)

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
        token = token_manager.token
        if token is None or token == "":
            QMessageBox.information(self.view, "提示", "请先登录")
            return
        if not self.data:
            QMessageBox.information(self.view, "提示", "请先加载数据")
            return

        # 清理临时文件夹
        if os.path.exists('temp'):
            shutil.rmtree('temp')

        print('准备上传数据:', self.data)

        new_list = self._process_data(self.data)
        API_URL = 'http://47.100.46.227:5586/api/internal/cost_ident/upload_oa'
        headers = {
            "Authorization": f"Bearer {token}"
        }

        result_data = []
        try:
            response = requests.post(API_URL, json=new_list, headers=headers)
            result = response.json()
            print('上传接口响应:', result)
            if result.get('code') == 200:
                if result.get('error_list') is None:
                    QMessageBox.information(self.view, "成功", "上传成功")
                else:
                    result_data = self._reserve_error_data(self.data, new_list, result.get('error_list', []))
                    QMessageBox.warning(self.view, "部分成功", f"{result.get('message')}。请查看预览数据后重新上传")
            else:
                raise ValueError(f"上传失败: {result.get('message')}")
        except Exception as e:
            QMessageBox.critical(self.view, "错误", f"上传请求失败: {e}, 请重新上传")
            return

        try:
            record_path = self.history_manager.save_upload_record(
                file_name=self.data_manager.file_name,
                data=self.data,
            )
            print(f"上传记录已保存: {record_path}")
        except Exception as e:
            print(f"保存上传记录失败: {e}")

        if result_data:
            self.set_data(result_data)
            self.data = result_data
        else:
            self.data = []
        # 发出最终上传信号
        self.data_manager.set_current_data(self.data)
        self.final_upload_requested.emit()

    def _process_data(self, data):
        new_list = []
        group_map = {}
        current_id = 1
        for row in data:
            key = (row.get("外销合同", ""), row.get("货币代码", ""))
            if key not in group_map:
                group_map[key] = current_id
                current_id += 1
            new_row = {"split_id": group_map[key], 'wxht': row.get("外销合同", ""), 'skdw': row.get("船代公司", ""),
                       'fymc': row.get("费用名称", ""), 'bb': row.get("货币代码", ""), 'je': float(row.get("金额", "")),
                       'bz': row.get("备注", "")}
            new_list.append(new_row)
        return new_list

    def _reserve_error_data(self, old_data, new_data, error_list):
        result = []
        for new_row in new_data:
            if new_row.get("split_id") in error_list:
                for old_row in old_data:
                    if (new_row.get("wxht") == old_row.get("外销合同") and
                            new_row.get("skdw") == old_row.get("船代公司") and
                            new_row.get("fymc") == old_row.get("费用名称") and
                            new_row.get("bb") == old_row.get("货币代码") and
                            float(new_row.get("je", 0)) == float(old_row.get("金额", 0)) and
                            new_row.get("bz") == old_row.get("备注")):
                        merged_row = new_row.copy()
                        merged_row["源文件"] = old_row.get("源文件", "")
                        result.append(old_row)
                        break
        return result
