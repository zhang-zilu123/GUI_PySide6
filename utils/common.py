"""
通用工具函数模块
提供项目中常用的辅助功能
"""
import os
import colorsys
import datetime
import shutil
from typing import List, Union, Optional, Dict

# 获取文件名列表
def get_filename_list(file_path: Union[str, List[str]]) -> List[str]:
    """获取文件名列表
    
    Args:
        file_path: 文件路径字符串或文件路径列表
        
    Returns:
        文件名列表
        
    Raises:
        TypeError: 当file_path类型不支持时
        ValueError: 当file_path为空时
    """
    try:
        if file_path is None:
            raise ValueError("file_path 不能为 None")

        if isinstance(file_path, list):
            if not file_path:
                return []
            # 如果是文件路径列表，返回所有文件名，过滤掉空值和None
            valid_paths = [path for path in file_path if path and isinstance(path, str)]
            return [os.path.basename(path.strip()) for path in valid_paths if path.strip()]
        elif isinstance(file_path, str):
            if not file_path.strip():
                return []
            # 如果是单个文件路径，返回包含单个文件名的列表
            return [os.path.basename(file_path.strip())]
        else:
            raise TypeError(f"不支持的file_path类型: {type(file_path)}")
    except Exception as e:
        print(f"获取文件名列表时出错: {str(e)}")
        return []

# 生成浅色系颜色
def generate_light_colors(count: int = 50, preset: Optional[List[str]] = None) -> List[str]:
    """生成浅色系颜色，循环使用预设颜色

    Args:
        count: 需要生成的颜色数量
        preset: 预设颜色列表

    Returns:
        生成的颜色列表（十六进制格式）
        
    Raises:
        ValueError: 当count小于0时
        TypeError: 当preset不是列表时
    """
    try:
        if count < 0:
            raise ValueError("颜色数量不能为负数")

        if count == 0:
            return []

        if preset is None:
            preset = [
                "#E3F2FD", "#E8F5E8", "#FFF3E0", "#F3E5F5", "#E0F2F1",
                "#FCE4EC", "#F1F8E9", "#EFEBE9", "#FAFAFA", "#E8EAF6"
            ]
        elif not isinstance(preset, list):
            raise TypeError("preset 必须是列表类型")
        elif not preset:
            # 如果preset为空列表，使用默认颜色
            preset = ["#FFFFFF"]  # 默认白色

        # 验证预设颜色格式
        valid_preset = []
        for color in preset:
            if isinstance(color, str) and color.startswith('#') and len(color) == 7:
                valid_preset.append(color)
            else:
                print(f"忽略无效颜色格式: {color}")

        if not valid_preset:
            valid_preset = ["#FFFFFF"]  # 如果没有有效颜色，使用白色

        # 循环遍历预设颜色
        colors = [valid_preset[i % len(valid_preset)] for i in range(count)]
        return colors

    except Exception as e:
        print(f"生成颜色时出错: {str(e)}")
        # 返回安全的默认颜色列表
        return ["#FFFFFF"] * max(0, count)

# 添加额外的浅色系颜色
def _generate_additional_colors(count: int) -> List[str]:
    """生成额外的浅色系颜色
    
    Args:
        count: 需要生成的颜色数量
        
    Returns:
        生成的颜色列表
        
    Raises:
        ValueError: 当count小于0时
    """
    try:
        if count < 0:
            raise ValueError("颜色数量不能为负数")

        if count == 0:
            return []

        additional_colors = []

        for i in range(count):
            try:
                # 生成蓝绿系浅色
                hue = 0.33 + (0.66 - 0.33) * (i / (count + 1)) if count > 0 else 0.5
                saturation = 0.4
                lightness = 0.9

                r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)

                # 确保RGB值在有效范围内
                r = max(0, min(1, r))
                g = max(0, min(1, g))
                b = max(0, min(1, b))

                hex_color = "#{:02x}{:02x}{:02x}".format(
                    int(r * 255), int(g * 255), int(b * 255)
                )
                additional_colors.append(hex_color)

            except Exception as color_error:
                print(f"生成第{i}个颜色时出错: {str(color_error)}")
                # 使用默认颜色
                additional_colors.append("#E8F4FD")

        return additional_colors

    except Exception as e:
        print(f"生成额外颜色时出错: {str(e)}")
        # 返回安全的默认颜色列表
        return ["#E8F4FD"] * max(0, count)

#  验证文件路径
def validate_file_path(file_path: str) -> bool:
    """验证文件路径是否有效
    
    Args:
        file_path: 要验证的文件路径
        
    Returns:
        文件路径是否有效
    """
    try:
        if not file_path or not isinstance(file_path, str):
            return False

        file_path = file_path.strip()
        if not file_path:
            return False

        # 检查路径是否存在
        return os.path.exists(file_path) and os.path.isfile(file_path)

    except Exception as e:
        print(f"验证文件路径时出错: {str(e)}")
        return False

# 获取文件大小
def safe_get_file_size(file_path: str) -> int:
    """安全地获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节），如果失败返回-1
    """
    try:
        if not validate_file_path(file_path):
            return -1

        return os.path.getsize(file_path)

    except Exception as e:
        print(f"获取文件大小时出错: {str(e)}")
        return -1

# 为文件名添加时间戳
def add_timestamp_to_filename(file_path: str) -> str:
    """为文件名添加时间戳并返回新文件路径"""
    dir_name, base_name = os.path.split(file_path)
    name, ext = os.path.splitext(base_name)
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    new_name = f"{name}_{timestamp}{ext}"
    new_path = os.path.join(dir_name, new_name)
    shutil.copy2(file_path, new_path)
    return new_path

# 计算多少个外销合同号
def count_outside_sales_contracts(data: Dict) -> int:
    """计算多少个外销合同号"""
    res = set()
    for item in data:
        if item.get("外销合同号"):
            res.add(item.get("外销合同号"))
    return len(res)
