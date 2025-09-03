"""
历史记录管理器
负责保存和读取上传记录
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any


class HistoryManager:
    """历史记录管理器"""

    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """确保data目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def save_upload_record(self, file_name: str, data: List[Dict]):
        """
        保存上传记录
        
        Args:
            file_name: 原始文件名
            data: 上传的数据列表

        Returns:
            str: 保存的文件路径
        """
        # 生成时间戳作为文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        record_filename = f"upload_{timestamp}.json"
        record_path = os.path.join(self.data_dir, record_filename)

        # 构建记录数据结构
        record_data = {
            "upload_time": datetime.now().isoformat(),
            "display_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "original_filename": file_name,
            "record_count": len(data),
            "data": data
        }

        # 保存到JSON文件
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=2)

        return record_path

    def load_upload_records(self) -> List[Dict]:
        """
        加载所有上传记录的列表（不包含具体数据）
        
        Returns:
            List[Dict]: 记录列表，每个元素包含基本信息
        """
        records = []

        if not os.path.exists(self.data_dir):
            return records

        # 遍历data目录下的所有JSON文件
        for filename in os.listdir(self.data_dir):
            if filename.startswith("upload_") and filename.endswith(".json"):
                file_path = os.path.join(self.data_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        record_data = json.load(f)

                    # 只保留列表显示需要的基本信息
                    record_info = {
                        "filename": filename,
                        "file_path": file_path,
                        "upload_time": record_data.get("upload_time"),
                        "display_time": record_data.get("display_time"),
                        "original_filename": record_data.get("original_filename"),
                        "record_count": record_data.get("record_count", 0)
                    }
                    records.append(record_info)
                except Exception as e:
                    print(f"读取记录文件失败: {filename}, 错误: {e}")

        # 按时间倒序排序（最新的在前面）
        records.sort(key=lambda x: x["upload_time"], reverse=True)
        return records

    def load_record_detail(self, file_path: str) -> Dict:
        """
        加载指定记录的详细数据
        
        Args:
            file_path: 记录文件路径
        
        Returns:
            Dict: 完整的记录数据
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取记录详情失败: {file_path}, 错误: {e}")
            return {}
