"""
基础样式定义文件
包含所有通用的样式变量和常量
"""

# 颜色系统
COLORS = {
    # 主色调 - 莫兰迪粉色系
    'primary': {
        50: '#fdf2f4',   # 最浅粉色
        100: '#fbe4e8',  # 浅粉色
        200: '#f5c5ce',  # 淡粉色
        300: '#eba6b3',  # 中浅粉色
        400: '#e18698',  # 中粉色
        500: '#d7677d',  # 主要品牌色
        600: '#c85469',  # 深粉色
        700: '#b94257',  # 深玫瑰色
        800: '#a93247',  # 暗玫瑰色
        900: '#982538',  # 最深玫瑰色
    },
    
    # 辅助色 - 莫兰迪蓝色系
    'secondary': {
        50: '#f0f4f8',   # 最浅蓝色
        100: '#e1e8f0',  # 浅蓝色
        200: '#c3d1e0',  # 淡蓝色
        300: '#a5b9d0',  # 中浅蓝色
        400: '#87a2c0',  # 中蓝色
        500: '#698ab0',  # 主要蓝色
        600: '#557399',  # 深蓝色
        700: '#425c82',  # 深灰蓝色
        800: '#30466b',  # 暗蓝色
        900: '#1e2f54',  # 最深蓝色
    },
    
    # 中性色 - 莫兰迪灰色系
    'neutral': {
        50: '#f7f7f7',    # 最浅背景
        100: '#efefef',   # 浅背景
        200: '#e4e4e4',   # 边框浅色
        300: '#d6d6d6',   # 边框中等
        400: '#b4b4b4',   # 禁用文本
        500: '#939393',   # 辅助文本
        600: '#737373',   # 主要文本
        700: '#525252',   # 标题文本
        800: '#404040',   # 深色背景
        900: '#262626',   # 最深背景
    },
    
    # 功能色 - 莫兰迪功能色系
    'success': '#8fb287',  # 莫兰迪绿
    'warning': '#e3b587',  # 莫兰迪橙
    'error': '#c67f7f',   # 莫兰迪红
    'info': '#8ca3b7',    # 莫兰迪蓝
}

# 字体系统
FONTS = {
    'family': '"PingFang SC", "Microsoft YaHei UI", "Segoe UI", sans-serif',
    'mono': '"SF Mono", "Cascadia Code", "Consolas", monospace',
    
    # 字号 - 调整为更合理的大小
    'size': {
        'xs': '12px',     # 辅助信息
        'sm': '13px',     # 小号文本
        'base': '14px',   # 基础文本
        'lg': '16px',     # 大号文本
        'xl': '18px',     # 副标题
        '2xl': '20px',    # 小标题
        '3xl': '24px',    # 主标题
    },
    
    # 行高
    'line_height': {
        'tight': 1.25,    # 紧凑
        'normal': 1.5,    # 正常
        'relaxed': 1.75,  # 宽松
    },
}

# 间距系统
SPACING = {
    'xs': '4px',      # 最小间距
    'sm': '8px',      # 小间距
    'md': '16px',     # 中等间距
    'lg': '24px',     # 大间距
    'xl': '32px',     # 超大间距
}

# 圆角
RADIUS = {
    'sm': '4px',      # 小圆角
    'md': '8px',      # 中等圆角
    'lg': '12px',     # 大圆角
    'xl': '16px',     # 超大圆角
    'full': '9999px', # 完全圆角
}

# 阴影
SHADOWS = {
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
}


# 基础组件样式
BASE_STYLES = {
    # 主窗口样式
    'main_window': f"""
        QMainWindow {{
            background-color: #ffffff;
            color: {COLORS['neutral'][700]};
            font-family: {FONTS['family']};
        }}
    """,
    
    # 标签页样式
    'tab_widget': f"""
        QTabWidget::pane {{
            border: none;
            background-color: #ffffff;
        }}
        
        QTabBar::tab {{
            background-color: #ffffff;
            color: {COLORS['neutral'][500]};
            padding: {SPACING['md']} {SPACING['lg']};
            border: 1px solid {COLORS['neutral'][200]};
            border-bottom: none;
            border-top-left-radius: {RADIUS['lg']};
            border-top-right-radius: {RADIUS['lg']};
            font-weight: 500;
            font-size: {FONTS['size']['base']};
            margin-right: {SPACING['xs']};
        }}
        
        QTabBar::tab:selected {{
            background-color: #ffffff;
            color: {COLORS['primary'][500]};
            border-bottom: 3px solid {COLORS['primary'][500]};
            font-weight: 600;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {COLORS['neutral'][50]};
            color: {COLORS['primary'][400]};
        }}
    """,
    
    # 按钮样式
    'button': {
        'primary': f"""
            QPushButton {{
                background-color: {COLORS['primary'][500]};
                color: #ffffff;
                border: none;
                border-radius: {RADIUS['md']};
                padding: 8px 16px;
                font-size: {FONTS['size']['base']};
                font-weight: 500;
                min-width: 50px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary'][600]};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary'][700]};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['neutral'][200]};
                color: {COLORS['neutral'][400]};
            }}
        """,
        
         'secondary': f"""
            QPushButton {{
                background-color: {COLORS['secondary'][500]};
                color: #ffffff;
                border: none;
                border-radius: {RADIUS['md']};
                padding: 8px 16px;
                font-size: {FONTS['size']['base']};
                font-weight: 500;
                min-width: 50px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary'][600]};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['secondary'][700]};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['neutral'][200]};
                color: {COLORS['neutral'][400]};
            }}
        """,
        
       'success': f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: #ffffff;
                border: none;
                border-radius: {RADIUS['md']};
                padding: 8px 16px;
                font-size: {FONTS['size']['base']};
                font-weight: 500;
                min-width: 50px;
            }}
            QPushButton:hover {{
                background-color: #7fa277;
            }}
            QPushButton:pressed {{
                background-color: #6f9267;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['neutral'][200]};
                color: {COLORS['neutral'][400]};
            }}
        """,
        
        'warning': f"""
            QPushButton {{
                background-color: {COLORS['warning']};
                color: #ffffff;
                border: none;
                border-radius: {RADIUS['md']};
                padding: 8px 16px;
                font-size: {FONTS['size']['base']};
                font-weight: 500;
                min-width: 50px;
            }}
            QPushButton:hover {{
                background-color: #d3a577;
            }}
            QPushButton:pressed {{
                background-color: #c39567;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['neutral'][200]};
                color: {COLORS['neutral'][400]};
            }}
        """,
        
        'danger': f"""
            QPushButton {{
                background-color: {COLORS['error']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: {FONTS['size']['base']};
                font-weight: 500;
                min-width: 50px;
               
            }}
            QPushButton:hover {{
                background-color: #b66f6f;
            }}
            QPushButton:pressed {{
                background-color: #a65f5f;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['neutral'][200]};
                color: {COLORS['neutral'][400]};
            }}
        """,
    },
    
    
    # 列表样式
    'list': f"""
        QListWidget {{
            border: 1px solid {COLORS['neutral'][200]};
            border-radius: {RADIUS['lg']};
            background-color: #ffffff;
            outline: none;
            font-size: {FONTS['size']['sm']};
        }}
        
        QListWidget::item {{
            padding: {SPACING['md']};
            border-bottom: 1px solid {COLORS['neutral'][100]};
            background-color: #ffffff;
        }}
        
        QListWidget::item:hover {{
            background-color: {COLORS['neutral'][50]};
        }}
        
        QListWidget::item:selected {{
            background-color: {COLORS['primary'][50]};
            color: {COLORS['primary'][700]};
            border: none;
        }}
        
        QListWidget::item:selected:hover {{
            background-color: {COLORS['primary'][100]};
        }}
    """,
    
    # 标签样式
    'label': {
        'title': f"""
            font-size: {FONTS['size']['2xl']};
            font-weight: bold;
            color: {COLORS['neutral'][900]};
            margin-bottom: {SPACING['md']};
        """,
        
        'subtitle': f"""
            font-size: {FONTS['size']['base']};
            font-weight: 200;
            color: {COLORS['neutral'][700]};
            margin-bottom: {SPACING['sm']};
        """,
        
        'description': f"""
            font-size: {FONTS['size']['base']};
            color: {COLORS['neutral'][500]};
            line-height: {FONTS['line_height']['relaxed']};
        """,
    },
    
    # 状态栏样式
    'status_bar': f"""
        QStatusBar {{
            background-color: #ffffff;
            color: {COLORS['neutral'][600]};
            border-top: 1px solid {COLORS['neutral'][200]};
            font-size: {FONTS['size']['sm']};
            padding: {SPACING['sm']} {SPACING['md']};
        }}
    """,
    
    # 滚动条样式
    'scrollbar': f"""
        QScrollBar:vertical {{
            background-color: #ffffff;
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {COLORS['neutral'][200]};
            border-radius: 6px;
            min-height: 30px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['neutral'][300]};
        }}
        
        QScrollBar:horizontal {{
            background-color: #ffffff;
            height: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {COLORS['neutral'][200]};
            border-radius: 6px;
            min-width: 30px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {COLORS['neutral'][300]};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
            height: 0;
            width: 0;
        }}
    """,

    
}