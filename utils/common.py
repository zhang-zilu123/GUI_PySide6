import os
import colorsys


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


def generate_light_colors(count=50):
    """
    生成指定数量的浅色系颜色
    """
    colors = []
    for i in range(count):
        # 生成HSL颜色，确保亮度较高（浅色）
        hue = i / count  # 色相在0-1之间
        saturation = 0.3 + (i % 3) * 0.1  # 饱和度适中
        lightness = 0.85 + (i % 2) * 0.05  # 高亮度确保浅色

        # 转换为RGB
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        # 转换为十六进制
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )
        colors.append(hex_color)

    return colors
