import os
import json
from PySide6.QtWidgets import QMessageBox


def write_mineru_config():
    src_json_path = os.path.join(os.path.dirname(__file__), "..", "config", "mineru.json")
    # 目标路径
    user_name = os.getlogin()
    dst_dir = os.path.join("C:\\Users", user_name)
    dst_json_path = os.path.join(dst_dir, "mineru.json")

    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if any('\u4e00' <= ch <= '\u9fff' for ch in project_dir):
        QMessageBox.critical(None, "错误",
                             "当前项目路径包含中文字符，可能导致模型加载失败，请将项目放置在不包含中文字符的路径下！")
        os._exit(1)

    # 检查目标文件是否存在
    if not os.path.exists(dst_json_path):
        # 检查源文件是否存在
        if not os.path.exists(src_json_path):
            raise FileNotFoundError(f"配置文件未找到: {src_json_path}")
        # 读取源文件内容
        with open(src_json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        # 修改 pipeline 路径为当前项目路径
        config["models-dir"]["pipeline"] = os.path.join(project_dir, "modelscope", "hub", "models", "OpenDataLab",
                                                        "PDF-Extract-Kit-1___0")
        # 写入目标文件
        with open(dst_json_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
