class DataManager:
    """数据管理器，负责在各个页面间传递和管理数据"""

    def __init__(self):
        self.current_data = []
        self.file_name = ""
        self.upload_history = []

    def set_current_data(self, data):
        """设置处理后的数据"""
        self.current_data = data

    def set_file_name(self, file_name):
        """设置当前处理的文件名"""
        self.file_name = file_name
