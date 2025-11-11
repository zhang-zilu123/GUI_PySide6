"""
应用程序主入口文件
创建QApplication实例和主窗口，启动应用程序事件循环
"""

import sys
import os

# 确保当前目录在 Python 路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from main_window import MainWindow
from utils.logger import setup_global_exception_handler, log_error

def main():
    """应用程序主函数"""
    try:
        # 设置全局异常处理器（在应用启动前）
        setup_global_exception_handler()

        # 创建QApplication实例，管理应用程序级别资源
        app = QApplication(sys.argv)

        # 设置应用程序名称
        app.setApplicationName("数据审核工具")
        app.setWindowIcon(QIcon("./assets/logo.svg"))

        # 创建主窗口
        window = MainWindow()

        # 显示主窗口
        window.show()

        # 启动应用程序事件循环，等待用户交互
        sys.exit(app.exec())

    except Exception as e:
        # 捕获主函数中的任何异常
        log_error("应用程序启动或运行时发生严重错误", e)
        print(f"\n应用程序发生严重错误: {str(e)}")
        print("详细信息已记录到错误日志文件")
        sys.exit(1)

if __name__ == "__main__":
    main()
