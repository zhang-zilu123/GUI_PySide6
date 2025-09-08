"""
应用程序主入口文件
创建QApplication实例和主窗口，启动应用程序事件循环
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from main_window import MainWindow


def main():
    """应用程序主函数"""
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


if __name__ == "__main__":
    main()
