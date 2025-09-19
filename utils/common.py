"""
通用工具函数模块
提供项目中常用的辅助功能
"""
import os
import colorsys
from typing import List, Union, Optional


def get_filename_list(file_path: Union[str, List[str]]) -> List[str]:
    """获取文件名列表
    
    Args:
        file_path: 文件路径字符串或文件路径列表
        
    Returns:
        文件名列表
    """
    if isinstance(file_path, list):
        # 如果是文件路径列表，返回所有文件名
        return [os.path.basename(path) for path in file_path if path]
    elif isinstance(file_path, str):
        # 如果是单个文件路径，返回包含单个文件名的列表
        return [os.path.basename(file_path)]
    else:
        return []


def generate_light_colors(count: int = 50, preset: Optional[List[str]] = None) -> List[str]:
    """生成浅色系颜色，前几个用预设颜色，剩下的自动生成
    
    Args:
        count: 需要生成的颜色数量
        preset: 预设颜色列表
        
    Returns:
        生成的颜色列表（十六进制格式）
    """
    if preset is None:
        preset = [
            "#E3F2FD", "#E8F5E8", "#FFF3E0", "#F3E5F5", "#E0F2F1",
            "#FCE4EC", "#F1F8E9", "#EFEBE9", "#FAFAFA", "#E8EAF6"
        ]

    # 使用预设颜色
    colors = preset[:min(count, len(preset))]

    # 如果需要更多颜色，自动生成
    remaining_count = count - len(colors)
    if remaining_count > 0:
        colors.extend(_generate_additional_colors(remaining_count))

    return colors[:count]


def _generate_additional_colors(count: int) -> List[str]:
    """生成额外的浅色系颜色
    
    Args:
        count: 需要生成的颜色数量
        
    Returns:
        生成的颜色列表
    """
    additional_colors = []
    
    for i in range(count):
        # 生成蓝绿系浅色
        hue = 0.33 + (0.66 - 0.33) * (i / (count + 1))
        saturation = 0.4
        lightness = 0.9
        
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )
        additional_colors.append(hex_color)

    return additional_colors
