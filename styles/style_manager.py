"""
样式管理器类
负责管理和应用应用程序的样式
"""
from PySide6.QtWidgets import QWidget, QPushButton, QLabel
from .base import BASE_STYLES, COLORS, FONTS, SPACING, RADIUS, SHADOWS
class StyleManager:
    """样式管理器类，负责管理和应用应用程序的样式"""
    
    @staticmethod
    def apply_base_style(widget: QWidget):
        """应用基础样式到窗口部件"""
        widget.setStyleSheet(BASE_STYLES['main_window'])
    
    @staticmethod
    def apply_button_style(button: QPushButton, style_type: str = 'primary'):
        """应用按钮样式
        
        Args:
            button: 要应用样式的按钮
            style_type: 按钮样式类型，可选值：primary, secondary, success, warning, danger
        """
        if style_type in BASE_STYLES['button']:
            button.setStyleSheet(BASE_STYLES['button'][style_type])
    
    @staticmethod
    def apply_label_style(label: QLabel, style_type: str = 'title'):
        """应用标签样式
        
        Args:
            label: 要应用样式的标签
            style_type: 标签样式类型，可选值：title, subtitle, description
        """
        if style_type in BASE_STYLES['label']:
            label.setStyleSheet(BASE_STYLES['label'][style_type])
    
    @staticmethod
    def apply_table_style(table):
        """应用表格样式"""
        table.setStyleSheet(BASE_STYLES['table'])
    
    @staticmethod
    def apply_list_style(list_widget):
        """应用列表样式"""
        list_widget.setStyleSheet(BASE_STYLES['list'])
    
    @staticmethod
    def apply_tab_style(tab_widget):
        """应用标签页样式"""
        tab_widget.setStyleSheet(BASE_STYLES['tab_widget'])
    
    @staticmethod
    def apply_status_bar_style(status_bar):
        """应用状态栏样式"""
        status_bar.setStyleSheet(BASE_STYLES['status_bar'])
    
    @staticmethod
    def apply_scrollbar_style(widget):
        """应用滚动条样式"""
        widget.setStyleSheet(BASE_STYLES['scrollbar'])
    
    @staticmethod
    def get_color(color_name: str, shade: int = 500) -> str:
        """获取颜色值
        
        Args:
            color_name: 颜色名称，如 'primary', 'neutral'
            shade: 色阶值，如 50, 100, 200 等
        
        Returns:
            str: 颜色的十六进制值
        """
        if color_name in COLORS:
            if isinstance(COLORS[color_name], dict) and shade in COLORS[color_name]:
                return COLORS[color_name][shade]
            elif isinstance(COLORS[color_name], str):
                return COLORS[color_name]
        return '#000000'  # 默认返回黑色
    
    @staticmethod
    def get_font_size(size_name: str) -> str:
        """获取字体大小
        
        Args:
            size_name: 字体大小名称，如 'xs', 'sm', 'base' 等
        
        Returns:
            str: 字体大小值，如 '12px'
        """
        return FONTS['size'].get(size_name, FONTS['size']['base'])
    
    @staticmethod
    def get_spacing(spacing_name: str) -> str:
        """获取间距值
        
        Args:
            spacing_name: 间距名称，如 'xs', 'sm', 'md' 等
        
        Returns:
            str: 间距值，如 '4px'
        """
        return SPACING.get(spacing_name, SPACING['md'])
    
    @staticmethod
    def get_radius(radius_name: str) -> str:
        """获取圆角值
        
        Args:
            radius_name: 圆角名称，如 'sm', 'md', 'lg' 等
        
        Returns:
            str: 圆角值，如 '4px'
        """
        return RADIUS.get(radius_name, RADIUS['md'])
    
    @staticmethod
    def get_shadow(shadow_name: str) -> str:
        """获取阴影值
        
        Args:
            shadow_name: 阴影名称，如 'sm', 'md', 'lg' 等
        
        Returns:
            str: 阴影值
        """
        return SHADOWS.get(shadow_name, SHADOWS['md'])
    
    