import os


def get_filename_list(file_path):
    """获取文件名列表"""
    if isinstance(file_path, list):
        # 如果是文件路径列表，返回所有文件名
        return [os.path.basename(path) for path in file_path if path]
    elif isinstance(file_path, str):
        # 如果是单个文件路径，返回包含单个文件名的列表
        return [os.path.basename(file_path)]
    else:
        return []

