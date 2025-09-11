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


def generate_light_colors(count=50, preset=None):
    """
    生成浅色系颜色，前几个用预设颜色，剩下的自动生成
    """
    import colorsys

    if preset is None:
        preset = [
            "#E3F2FD", "#E8F5E8", "#FFF3E0", "#F3E5F5", "#E0F2F1",
            "#FCE4EC", "#F1F8E9", "#EFEBE9", "#FAFAFA", "#E8EAF6"
        ]

    colors = preset[:count]

    for i in range(max(0, count - len(colors))):
        hue = 0.33 + (0.66 - 0.33) * (i / (count - len(colors) + 1))  # 蓝绿系
        saturation = 0.4
        lightness = 0.9
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )
        colors.append(hex_color)

    return colors
