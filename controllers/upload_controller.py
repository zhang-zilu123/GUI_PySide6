"""
上传功能控制器
处理文件上传相关的业务逻辑

"""
import os
import shutil
import json
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import QObject, Signal, QThread
from utils.mineru_parse import parse_doc
from utils.model_md_to_json import extract_info_from_md
from config.config import EXTRA_FIELD


class ExtractDataWorker(QThread):
    """数据提取工作线程"""
    finished = Signal(str, dict, bool, str) 
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        
    def run(self):
        """在线程中执行耗时操作"""
        try:
            # 提取数据
            data = self._extract_data_from_pdf(self.file_path)
            self.finished.emit(self.file_path, data, True, "")
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            self.finished.emit(self.file_path, {}, False, error_msg)
    
    def _extract_data_from_pdf(self, file_path):
        """从PDF文件中提取数据"""
        # 这里应该是实际的PDF解析逻辑
        os.environ['MINERU_MODEL_SOURCE'] = 'local'
        path_list = [file_path]
        # 解析pdf
        parse_doc(path_list=path_list, output_dir="./output", backend="pipeline")
        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)
        md_path = os.path.join("./output", name, "auto", f"{name}.md")
        # 大模型解析md文件
        info_dict = extract_info_from_md(md_path)

        if isinstance(info_dict, str):
            try:
                info_dict = json.loads(info_dict)
            except json.JSONDecodeError:
                info_dict = {}

        print(f"解析md文件: {info_dict}")
        if os.path.exists('./output'):
            shutil.rmtree('./output')
            print('删除临时文件夹 ./output')


        # 构建返回数据
        display_data = {}
        for field_name in EXTRA_FIELD:
            # 从info_dict中获取对应字段的值，如果不存在则为空字符串
            if info_dict.get(field_name) is not None:
                display_data[field_name] = str(info_dict[field_name])
            else:
                display_data[field_name] = ""
            
        print(f"返回数据: {display_data}")

        return display_data

class UploadController(QObject):
    """上传功能控制器"""
    # 定义信号：当文件处理完成时发出
    file_processed = Signal(str, dict)  # 参数为文件路径和处理后的数据
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
        for file_path in file_paths:
            if self._process_file(file_path):  # 验证文件格式
                self._add_file_to_list(file_path)
            
    def _open_file_dialog(self):
        """打开文件选择对话框"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.view,
            "选择文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )

        if file_paths:
            for file_path in file_paths:
                if self._process_file(file_path):  # 验证文件格式
                    self._add_file_to_list(file_path)
    def show_file_list(self):
        """显示文件列表，隐藏上传信息框"""
        self.view.upload_frame.setVisible(False)
        self.view.file_list.setVisible(True)
        self.view.clear_button.setVisible(True)
    def hide_file_list(self):
        """隐藏文件列表，显示上传信息框"""
        self.view.upload_frame.setVisible(True)
        self.view.file_list.setVisible(False)
        self.view.clear_button.setVisible(False)

    def _add_file_to_list(self, file_path):
        """添加文件到上传列表"""
        if file_path not in self.uploaded_files:
            self.uploaded_files.append(file_path)
            self.add_uploaded_file(file_path)

    def add_uploaded_file(self, file_path):
        """添加上传的文件到列表"""
        file_name = os.path.basename(file_path)
        self.view.file_list.addItem(file_name)
        
        # 显示文件列表，隐藏上传信息框
        self.show_file_list()
        
        # 显示分析按钮
        self.view.analyze_button.setVisible(True)
        
        # 更新上传按钮文字
        self.view.upload_button.setText("继续上传")

        self.view.instruction.setText(f"可点击'继续上传'增加需要提取的文件或者点击'开始分析'提取数据")
    

    def clear_file_list(self):
        """清空文件列表"""
        self.uploaded_files.clear()
        self.view.file_list.clear()
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
            
            # 为每个文件创建一个工作线程
            for file_path in self.uploaded_files:
                worker = ExtractDataWorker(file_path)
                worker.finished.connect(self._on_worker_finished)
                worker.start()
                self.current_workers.append(worker)
    

    def _disable_ui_controls(self):
        """禁用界面控件"""
        self.view.upload_button.setEnabled(False)
        self.view.analyze_button.setEnabled(False)
        self.view.clear_button.setEnabled(False)
        self.view.file_list.setEnabled(False)
        # 禁用上传区域的点击事件
        self.view.upload_frame.setEnabled(False)

    def _enable_ui_controls(self):
        """启用界面控件"""
        self.view.upload_button.setEnabled(True)
        self.view.analyze_button.setEnabled(True)
        self.view.clear_button.setEnabled(True)
        self.view.file_list.setEnabled(True)
        # 启用上传区域的点击事件
        self.view.upload_frame.setEnabled(True)

    def _on_worker_finished(self, file_path, data, success, error_msg):
        """处理工作线程完成事件"""
        # 从当前工作线程列表中移除已完成的线程
        sender = self.sender()
        if sender in self.current_workers:
            self.current_workers.remove(sender)
        
        if success:
            # 发出文件处理完成信号
            self.file_processed.emit(file_path, data)
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
            self._add_file_to_list(file_path)
            return True  # 表示处理成功

        except Exception as e:
            error_msg = f"验证文件时出错: {str(e)}"
            QMessageBox.critical(self.view, "错误", error_msg)
            return False

