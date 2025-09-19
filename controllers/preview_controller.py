"""
预览功能控制器
处理数据预览相关的业务逻辑
"""
import json
import os
import shutil
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs

import requests
from PySide6.QtCore import QObject, Signal, Qt, QUrl
from PySide6.QtWidgets import (QVBoxLayout, QDialog, QMessageBox)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from config.config import SUBMIT_FIELD
from data.history_manager import HistoryManager
from data.token_manager import token_manager


class LoginDialog(QDialog):
    """登录弹窗，包含WebEngineView用于扫码登录操作"""

    login_success = Signal()

    def __init__(self, parent=None):
        """初始化登录对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("系统登录")
        self.network_manager = QNetworkAccessManager(self)
        self.resize(800, 600)
        self._setup_ui()
        self.get_login_url()

    def _setup_ui(self) -> None:
        """初始化UI布局和WebEngineView"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        # 监听页面跳转
        self.web_view.urlChanged.connect(self.on_url_changed)

    def get_login_url(self) -> None:
        """请求后端获取扫码登录页面URL"""
        api_url = 'http://47.100.46.227:5586/api/login/qw_login_url?next=/chat'
        request = QNetworkRequest(QUrl(api_url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        request.setRawHeader(b"User-Agent", b"PySide6 Network Client")
        reply = self.network_manager.get(request)
        reply.finished.connect(self.handle_get_url_response)

    def handle_get_url_response(self) -> None:
        """处理扫码登录页面URL的响应"""
        reply = self.sender()
        if not isinstance(reply, QNetworkReply):
            return

        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                self._handle_successful_url_response(reply)
            else:
                QMessageBox.critical(self, "错误", "网络连接失败")
        finally:
            reply.deleteLater()

    def _handle_successful_url_response(self, reply: QNetworkReply) -> None:
        """处理成功的URL响应
        
        Args:
            reply: 网络回复对象
        """
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

    def on_url_changed(self, qurl: QUrl) -> None:
        """监听扫码后页面跳转，获取code和state参数并请求后端登录
        
        Args:
            qurl: 新的URL
        """
        url = qurl.toString()
        print("页面跳转到：", url)

        if "/login2" in url:
            self._handle_login_redirect(url)

    def _handle_login_redirect(self, url: str) -> None:
        """处理登录重定向
        
        Args:
            url: 重定向URL
        """
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            code = params.get("code", [""])[0]
            state = params.get("state", [""])[0]

            # 构造登录请求
            self._send_login_request(code, state)

        except Exception as e:
            QMessageBox.warning(self, "错误", f"处理登录重定向失败: {e}")

    def _send_login_request(self, code: str, state: str) -> None:
        """发送登录请求
        
        Args:
            code: 授权码
            state: 状态参数
        """
        api_url = 'http://47.100.46.227:5586/api/login/qw_login'
        request = QNetworkRequest(QUrl(api_url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")

        payload = {'code': code, 'state': state}
        json_data = json.dumps(payload).encode('utf-8')
        reply = self.network_manager.post(request, json_data)
        reply.finished.connect(self.handle_login_response)

    def handle_login_response(self) -> None:
        """处理扫码登录后的后端响应，保存token并关闭弹窗"""
        reply = self.sender()
        if not isinstance(reply, QNetworkReply):
            return

        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                self._handle_successful_login(reply)
            else:
                QMessageBox.critical(self, "错误", "网络连接失败")
        finally:
            reply.deleteLater()

    def _handle_successful_login(self, reply: QNetworkReply) -> None:
        """处理成功的登录响应
        
        Args:
            reply: 网络回复对象
        """
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


class PreviewController(QObject):
    """预览功能控制器
    
    负责处理数据预览和上传相关的业务逻辑：
    - 数据预览展示
    - 用户登录管理
    - 数据上传处理
    - 历史记录管理
    """

    # 信号定义
    final_upload_requested = Signal()
    back_to_edit_requested = Signal()
    continue_upload_requested = Signal()

    def __init__(self, view, data_manager):
        """初始化预览控制器
        
        Args:
            view: 预览视图对象
            data_manager: 数据管理器
        """
        super().__init__()
        self.view = view
        self.data_manager = data_manager
        self.data: Optional[List[Dict[str, Any]]] = None
        self.history_manager = HistoryManager()
        self.dialog: Optional[LoginDialog] = None
        self._connect_signals()

    def _connect_signals(self) -> None:
        """连接视图信号"""
        self.view.back_button.clicked.connect(lambda: self.back_to_edit_requested.emit())
        self.view.upfile_button.clicked.connect(lambda: self.continue_upload_requested.emit())
        self.view.upload_button.clicked.connect(self._on_upload_clicked)
        self.view.load_button.clicked.connect(self._on_load_button_clicked)

    def _on_load_button_clicked(self) -> None:
        """处理登录按钮点击事件"""
        self.dialog = LoginDialog(self.view)
        self.dialog.login_success.connect(self._on_login_success)
        self.dialog.show()

    def _on_login_success(self) -> None:
        """处理登录成功事件"""
        token = token_manager.token
        if token:
            self.view.load_button.setVisible(False)

    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """设置要预览的数据
        
        Args:
            data: 要预览的数据列表
        """
        self.data = data
        self._load_data_to_table()
        self._update_summary()

    def _load_data_to_table(self) -> None:
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
        self._populate_preview_table(data_list)

    def _populate_preview_table(self, data_list: List[Dict[str, Any]]) -> None:
        """填充预览表格数据
        
        Args:
            data_list: 数据列表
        """
        field_keys = ["外销合同", "船代公司", "费用名称", "货币代码", "金额", "备注"]

        for row, item in enumerate(data_list):
            for col, field_key in enumerate(field_keys):
                value = str(item.get(field_key, ""))
                table_item = self.view.create_table_item(value)
                self.view.preview_table.setItem(row, col, table_item)

    def _update_summary(self) -> None:
        """更新摘要信息"""
        if not self.data:
            self.view.summary_text.setPlainText("暂无数据")
            return

        data_count = len(self.data)
        filename = self.data_manager.file_name or "未知文件"
        summary_text = f"记录数: {data_count}\n文件名:{filename} \n状态: 已审核\n准备上传"
        self.view.summary_text.setPlainText(summary_text)

    def _on_upload_clicked(self) -> None:
        """处理上传按钮点击事件"""
        # 验证登录状态
        if not self._validate_login():
            return

        # 验证数据
        if not self._validate_data():
            return

        # 执行上传
        self._perform_upload()

    def _validate_login(self) -> bool:
        """验证登录状态
        
        Returns:
            是否已登录
        """
        token = token_manager.token
        if token is None or token == "":
            QMessageBox.information(self.view, "提示", "请先登录")
            return False
        return True

    def _validate_data(self) -> bool:
        """验证数据
        
        Returns:
            数据是否有效
        """
        if not self.data:
            QMessageBox.information(self.view, "提示", "请先加载数据")
            return False
        return True

    def _perform_upload(self) -> None:
        """执行上传操作"""
        # 清理临时文件夹
        self._cleanup_temp_files()

        print('准备上传数据:', self.data)

        # 处理数据并上传
        processed_data = self._process_data(self.data)
        upload_result = self._upload_to_server(processed_data)

        if upload_result is not None:
            self._handle_upload_result(upload_result, processed_data)

    def _cleanup_temp_files(self) -> None:
        """清理临时文件"""
        if os.path.exists('temp'):
            shutil.rmtree('temp')

    def _upload_to_server(self, processed_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """上传数据到服务器
        
        Args:
            processed_data: 处理后的数据
            
        Returns:
            上传结果或None（如果失败）
        """
        API_URL = 'http://47.100.46.227:5586/api/internal/cost_ident/upload_oa'
        headers = {"Authorization": f"Bearer {token_manager.token}"}

        try:
            response = requests.post(API_URL, json=processed_data, headers=headers)
            result = response.json()
            print('上传接口响应:', result)
            return result
        except Exception as e:
            QMessageBox.critical(self.view, "错误", f"上传请求失败: {e}, 请重新上传")
            return None

    def _handle_upload_result(self, result: Dict[str, Any], processed_data: List[Dict[str, Any]]) -> None:
        """处理上传结果
        
        Args:
            result: 上传结果
            processed_data: 处理后的数据
        """
        error_list = []

        if result.get('code') == 200:
            error_list = result.get('error_list', [])
            if error_list is None:
                QMessageBox.information(self.view, "成功", "上传成功")
            else:
                QMessageBox.warning(self.view, "部分成功",
                                    f"{result.get('message')}。请查看预览数据后重新上传")
        else:
            QMessageBox.critical(self.view, "错误", f"上传失败: {result.get('message')}")
            return

        # 处理结果数据
        self._process_upload_result(error_list, processed_data, result)

    def _process_upload_result(self, error_list: List[Any], processed_data: List[Dict[str, Any]],
                               result: Dict[str, Any]) -> None:
        """处理上传结果数据
        
        Args:
            error_list: 错误列表
            processed_data: 处理后的数据
            result: 上传结果
        """
        save_data = self.data

        if error_list:
            # 保留上传失败的数据
            result_data = self._reserve_error_data(self.data, processed_data, error_list)
            save_data = self._mark_error(self.data, result)
            self.set_data(result_data)
            self.data = result_data
        else:
            # 标记所有数据为成功
            for item in save_data:
                item["is_error"] = False
            self.data = []

        # 保存上传记录
        self._save_upload_record(save_data)

        # 发出最终上传信号
        self.data_manager.set_current_data(self.data)
        self.final_upload_requested.emit()

    def _save_upload_record(self, save_data: List[Dict[str, Any]]) -> None:
        """保存上传记录
        
        Args:
            save_data: 要保存的数据
        """
        try:
            record_path = self.history_manager.save_upload_record(
                file_name=self.data_manager.file_name,
                data=save_data,
            )
            print(f"上传记录已保存: {record_path}")
        except Exception as e:
            print(f"保存上传记录失败: {e}")

    def _process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理数据格式以符合API要求
        
        Args:
            data: 原始数据
            
        Returns:
            处理后的数据
        """
        new_list = []
        group_map = {}
        current_id = 1

        for row in data:
            key = (row.get("外销合同", ""), row.get("货币代码", ""))
            if key not in group_map:
                group_map[key] = current_id
                current_id += 1

            new_row = {
                "split_id": group_map[key],
                'wxht': row.get("外销合同", ""),
                'skdw': row.get("船代公司", ""),
                'fymc': row.get("费用名称", ""),
                'bb': row.get("货币代码", ""),
                'je': float(row.get("金额", 0)),
                'bz': row.get("备注", "")
            }
            new_list.append(new_row)

        return new_list

    def _reserve_error_data(self, old_data: List[Dict[str, Any]],
                            new_data: List[Dict[str, Any]],
                            error_list: List[Any]) -> List[Dict[str, Any]]:
        """保留错误数据
        
        Args:
            old_data: 原始数据
            new_data: 处理后的数据
            error_list: 错误列表
            
        Returns:
            保留的错误数据
        """
        result = []
        for new_row in new_data:
            if new_row.get("split_id") in error_list:
                for old_row in old_data:
                    if self._rows_match(new_row, old_row):
                        result.append(old_row)
                        break
        return result

    def _rows_match(self, new_row: Dict[str, Any], old_row: Dict[str, Any]) -> bool:
        """检查新旧行是否匹配
        
        Args:
            new_row: 新行数据
            old_row: 旧行数据
            
        Returns:
            是否匹配
        """
        return (new_row.get("wxht") == old_row.get("外销合同") and
                new_row.get("skdw") == old_row.get("船代公司") and
                new_row.get("fymc") == old_row.get("费用名称") and
                new_row.get("bb") == old_row.get("货币代码") and
                float(new_row.get("je", 0)) == float(old_row.get("金额", 0)) and
                new_row.get("bz") == old_row.get("备注"))

    def _mark_error(self, old_data: List[Dict[str, Any]],
                    result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """标记错误数据
        
        Args:
            old_data: 原始数据
            result: 上传结果
            
        Returns:
            标记后的数据
        """
        result_list = []
        result_set = [tuple(sorted(item.items())) for item in result.get('data', [])]

        for item in old_data:
            item_copy = item.copy()
            item_tuple = tuple(sorted(item.items()))
            item_copy["is_error"] = item_tuple in result_set
            result_list.append(item_copy)

        return result_list
