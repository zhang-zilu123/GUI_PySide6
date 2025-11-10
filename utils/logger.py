"""
统一日志管理模块
提供灵活的日志配置，支持：
1. 多个日志记录器，可以记录到不同的日志文件
2. 统一的日志格式
3. 自动创建日志目录
4. 防止重复添加处理器
"""

import logging
import os
from datetime import datetime
from typing import Optional

class LoggerManager:
    """日志管理器"""

    # 存储已创建的 logger 实例，避免重复创建
    _loggers = {}
    # 日志目录
    LOG_DIR = "./log"

    @classmethod
    def get_logger(
            cls, name: str, log_file: Optional[str] = None, level: int = logging.INFO
    ) -> logging.Logger:
        """获取或创建日志记录器

        Args:
            name: 日志记录器名称
            log_file: 日志文件名（可选）。如果不提供，将使用 name 作为文件名
            level: 日志级别，默认为 INFO

        Returns:
            logging.Logger: 配置好的日志记录器

        Examples:
            # 创建上传模块的日志记录器
            upload_logger = LoggerManager.get_logger('upload', 'upload.log')

            # 创建文件转换模块的日志记录器，与上传模块共享同一个日志文件
            convert_logger = LoggerManager.get_logger('file_conversion', 'upload.log')

            # 创建独立的历史记录日志
            history_logger = LoggerManager.get_logger('history', 'history.log')
        """
        # 创建日志目录
        os.makedirs(cls.LOG_DIR, exist_ok=True)

        # 如果没有指定日志文件，使用 name 作为文件名
        if log_file is None:
            current_time = datetime.now().strftime("%Y%m%d-%H%M")
            log_file = f"{current_time}-{name}.log"

        # 构建完整的日志文件路径
        log_path = os.path.join(cls.LOG_DIR, log_file)

        # 使用日志文件路径作为唯一标识，确保写入同一文件的 logger 共享配置
        logger_key = log_path

        # 如果已经存在该 logger，直接返回
        if logger_key in cls._loggers:
            return cls._loggers[logger_key]

        # 创建新的 logger
        logger = logging.getLogger(logger_key)
        logger.setLevel(level)

        # 防止日志向上传播到父 logger
        logger.propagate = False

        # 检查是否已经有处理器（避免重复添加）
        if not logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(level)

            # 日志格式
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)

            # 添加处理器
            logger.addHandler(file_handler)

        # 缓存 logger
        cls._loggers[logger_key] = logger

        return logger

    @classmethod
    def get_shared_logger(
            cls, name: str, shared_log_name: str = "app"
    ) -> logging.Logger:
        """获取共享日志记录器（多个模块写入同一个日志文件）

        Args:
            name: 模块名称（用于日志中标识来源）
            shared_log_name: 共享日志文件的基础名称

        Returns:
            logging.Logger: 配置好的日志记录器

        Examples:
            # 多个模块共享同一个日志文件
            upload_logger = LoggerManager.get_shared_logger('upload', 'app')
            convert_logger = LoggerManager.get_shared_logger('file_conversion', 'app')
            # 它们都会写入到同一个 app.log 文件
        """
        current_time = datetime.now().strftime("%Y%m%d-%H%M")
        log_file = f"{current_time}-{shared_log_name}.log"
        return cls.get_logger(name, log_file)

    @classmethod
    def add_console_handler(
            cls, logger: logging.Logger, level: int = logging.INFO
    ) -> None:
        """为日志记录器添加控制台输出

        Args:
            logger: 日志记录器
            level: 控制台输出的日志级别
        """
        # 检查是否已经有控制台处理器
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                    handler, logging.FileHandler
            ):
                return  # 已存在控制台处理器

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    @classmethod
    def cleanup(cls) -> None:
        """清理所有日志记录器（用于程序退出时）"""
        for logger in cls._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        cls._loggers.clear()

# ==================== 预定义的日志记录器 ====================


def get_upload_logger() -> logging.Logger:
    """获取上传模块的日志记录器"""
    current_time = datetime.now().strftime("%Y%m%d-%H%M")
    log_file = f"{current_time}-上传文件.log"
    logger = LoggerManager.get_logger("upload", log_file)

    # 记录设备ID（仅第一次创建时）
    if not hasattr(get_upload_logger, "_device_logged"):
        try:
            with open("./device_id.txt", "r", encoding="utf-8") as f:
                content = f.read().strip()
                logger.info(f"device_id: {content}")
            get_upload_logger._device_logged = True
        except Exception as e:
            logger.error(f"无法读取 device_id: {e}")

    return logger

def get_file_conversion_logger() -> logging.Logger:
    """获取文件转换模块的日志记录器（与上传模块共享日志文件）"""
    current_time = datetime.now().strftime("%Y%m%d-%H%M")
    log_file = f"{current_time}-上传文件.log"
    return LoggerManager.get_logger("file_conversion", log_file)

def get_history_logger() -> logging.Logger:
    """获取历史记录模块的日志记录器"""
    current_time = datetime.now().strftime("%Y%m%d-%H%M")
    log_file = f"{current_time}-历史记录.log"
    return LoggerManager.get_logger("history", log_file)

def get_edit_logger() -> logging.Logger:
    """获取编辑模块的日志记录器"""
    current_time = datetime.now().strftime("%Y%m%d-%H%M")
    log_file = f"{current_time}-编辑.log"
    return LoggerManager.get_logger("edit", log_file)

def get_preview_logger() -> logging.Logger:
    """获取预览模块的日志记录器"""
    current_time = datetime.now().strftime("%Y%m%d-%H%M")
    log_file = f"{current_time}-提交至OA数据库.log"
    logger = LoggerManager.get_logger("preview", log_file)

    # 记录设备ID（仅第一次创建时）
    if not hasattr(get_preview_logger, "_device_logged"):
        try:
            with open("./device_id.txt", "r", encoding="utf-8") as f:
                content = f.read().strip()
                logger.info(f"device_id: {content}")
            get_preview_logger._device_logged = True
        except Exception as e:
            logger.error(f"无法读取 device_id: {e}")
    return logger

def get_error_logger() -> logging.Logger:
    """获取错误日志记录器（专门记录系统错误）"""
    current_time = datetime.now().strftime("%Y%m%d-%H%M")
    log_file = f"{current_time}-错误日志.log"
    logger = LoggerManager.get_logger("error", log_file, level=logging.ERROR)

    # 记录设备ID（仅第一次创建时）
    if not hasattr(get_error_logger, "_device_logged"):
        try:
            with open("./device_id.txt", "r", encoding="utf-8") as f:
                content = f.read().strip()
                logger.error(f"device_id: {content}")
            get_error_logger._device_logged = True
        except Exception as e:
            logger.error(f"无法读取 device_id: {e}")

    return logger

def upload_all_logs() -> dict:
    """上传所有日志文件到OSS

    上传以下日志文件：
    - 上传文件日志（upload + file_conversion）
    - 提交至OA数据库日志（preview）
    - 错误日志（error）

    Returns:
        dict: 上传结果，格式为 {
            'success': bool,
            'uploaded_files': list,
            'failed_files': list,
            'error_message': str
        }
    """
    from utils.upload_file_to_oss import up_local_file

    current_time = datetime.now().strftime("%Y%m%d-%H%M")

    # 需要上传的日志文件列表
    log_files = [
        f"./log/{current_time}-上传文件.log",  # upload + file_conversion
        f"./log/{current_time}-提交至OA数据库.log",  # preview
        f"./log/{current_time}-错误日志.log",  # error
    ]

    for log_file in log_files:
        if os.path.exists(log_file):
            up_local_file(log_file, object_prefix='chatbot_25_0528/muai-models/cost_ident/log')

# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 示例1：使用预定义的日志记录器
    upload_logger = get_upload_logger()
    upload_logger.info("这是上传模块的日志")

    # 示例2：文件转换模块使用相同的日志文件
    convert_logger = get_file_conversion_logger()
    convert_logger.info("这是文件转换模块的日志，会写入同一个文件")

    # 示例3：使用错误日志记录器
    error_logger = get_error_logger()
    error_logger.error("这是一个系统错误")
    error_logger.critical("这是一个严重错误")

    # 示例4：使用预览日志记录器
    preview_logger = get_preview_logger()
    preview_logger.info("提交数据到OA数据库")

    # 示例5：创建自定义日志记录器
    custom_logger = LoggerManager.get_logger("custom_module", "custom.log")
    custom_logger.info("这是自定义模块的日志")

    # 示例6：为日志记录器添加控制台输出
    LoggerManager.add_console_handler(upload_logger)
    upload_logger.info("这条日志会同时输出到文件和控制台")

    # 示例7：多个模块共享一个日志文件
    module1_logger = LoggerManager.get_shared_logger("module1", "shared")
    module2_logger = LoggerManager.get_shared_logger("module2", "shared")
    module1_logger.info("模块1的日志")
    module2_logger.info("模块2的日志")  # 写入同一个文件

    # 示例8：上传所有日志文件
    print("\n" + "=" * 60)
    print("上传所有日志文件到OSS")
    print("=" * 60)
    # result = upload_all_logs()
    # print(f"上传结果: {result}")
