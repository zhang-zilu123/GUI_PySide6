"""
阿里云OSS文件上传工具模块
提供安全可靠的文件上传功能
"""
import os
import logging
from typing import Optional

# 设置日志
logger = logging.getLogger(__name__)

try:
    import alibabacloud_oss_v2 as oss
except ImportError as e:
    logger.error(f"导入alibabacloud_oss_v2失败: {e}")
    oss = None

try:
    from dotenv import load_dotenv
except ImportError as e:
    logger.error(f"导入dotenv失败: {e}")
    load_dotenv = None


def up_local_file(local_file_path: str, bucket_name: str = 'muai-models', 
                  object_prefix: str = 'chatbot_25_0528/muai-models/cost_ident') -> str:
    """上传本地文件到阿里云OSS
    
    Args:
        local_file_path: 本地文件路径
        bucket_name: OSS存储桶名称
        object_prefix: 对象前缀路径
        
    Returns:
        上传成功后的对象键名
        
    Raises:
        FileNotFoundError: 本地文件不存在
        ValueError: 参数无效
        RuntimeError: 上传失败
        ConnectionError: 网络连接失败
    """
    try:
        # 参数验证
        if not local_file_path or not isinstance(local_file_path, str):
            raise ValueError("本地文件路径无效")
            
        if not bucket_name or not isinstance(bucket_name, str):
            raise ValueError("存储桶名称无效")
            
        # 检查依赖
        if oss is None:
            raise RuntimeError("alibabacloud_oss_v2库未安装，无法进行文件上传")
            
        if load_dotenv is None:
            logger.warning("dotenv库未安装，将尝试直接从环境变量读取配置")
        else:
            load_dotenv()
            
        # 检查本地文件
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"本地文件不存在: {local_file_path}")
            
        if not os.path.isfile(local_file_path):
            raise ValueError(f"路径不是文件: {local_file_path}")
            
        # 检查文件大小
        file_size = os.path.getsize(local_file_path)
        if file_size == 0:
            raise ValueError("文件为空，无法上传")
        elif file_size > 5 * 1024 * 1024 * 1024:  # 5GB限制
            raise ValueError(f"文件太大 ({file_size / 1024 / 1024 / 1024:.1f}GB)，超过5GB限制")
            
        # 检查环境变量
        access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
        access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
        
        if not access_key_id or not access_key_secret:
            raise ValueError("OSS访问密钥未配置，请设置OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET环境变量")
            
        # 设置环境变量（确保SDK能读取到）
        os.environ["OSS_ACCESS_KEY_ID"] = access_key_id
        os.environ["OSS_ACCESS_KEY_SECRET"] = access_key_secret
        
        # 创建OSS客户端
        try:
            credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
            cfg = oss.config.load_default()
            cfg.credentials_provider = credentials_provider
            cfg.region = 'cn-shanghai'
            cfg.connect_timeout = 30  # 30秒连接超时
            cfg.read_timeout = 300   # 5分钟读取超时
            
            client = oss.Client(cfg)
        except Exception as e:
            raise ConnectionError(f"创建OSS客户端失败: {str(e)}")
            
        # 生成对象键名
        file_name = os.path.basename(local_file_path)
        if not file_name:
            raise ValueError("无法从文件路径提取文件名")
            
        object_key = f"{object_prefix}/{file_name}" if object_prefix else file_name
        
        # 执行上传
        try:
            with open(local_file_path, 'rb') as f:
                logger.info(f"开始上传文件: {local_file_path} -> {object_key}")
                
                result = client.put_object(oss.PutObjectRequest(
                    bucket=bucket_name,
                    key=object_key,
                    body=f,
                ))
                
                # 检查上传结果
                if not (200 <= result.status_code < 300):
                    raise RuntimeError(f"上传失败，状态码: {result.status_code}")
                    
                logger.info(f"文件上传成功: {object_key}, 状态码: {result.status_code}")
                return object_key
                
        except IOError as e:
            raise RuntimeError(f"读取本地文件失败: {str(e)}")
        except Exception as e:
            if "network" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"网络连接失败: {str(e)}")
            else:
                raise RuntimeError(f"上传过程中出错: {str(e)}")
                
    except Exception as e:
        error_msg = f"上传文件到OSS失败 {local_file_path}: {str(e)}"
        logger.error(error_msg)
        raise


def check_oss_connectivity(bucket_name: str = 'muai-models') -> bool:
    """检查OSS连接性
    
    Args:
        bucket_name: 存储桶名称
        
    Returns:
        连接是否正常
    """
    try:
        if oss is None:
            logger.error("OSS库未安装")
            return False
            
        # 检查环境变量
        access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
        access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
        
        if not access_key_id or not access_key_secret:
            logger.error("OSS访问密钥未配置")
            return False
            
        # 设置环境变量
        os.environ["OSS_ACCESS_KEY_ID"] = access_key_id
        os.environ["OSS_ACCESS_KEY_SECRET"] = access_key_secret
        
        # 创建客户端并测试连接
        credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials_provider
        cfg.region = 'cn-shanghai'
        cfg.connect_timeout = 10  # 10秒超时
        
        client = oss.Client(cfg)
        
        # 尝试列举存储桶（测试连接）
        try:
            client.list_objects_v2(oss.ListObjectsV2Request(
                bucket=bucket_name,
                max_keys=1
            ))
            logger.info("OSS连接测试成功")
            return True
        except Exception as e:
            logger.error(f"OSS连接测试失败: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"检查OSS连接性时出错: {str(e)}")
        return False


def get_file_upload_progress(file_size: int) -> dict:
    """获取文件上传进度信息
    
    Args:
        file_size: 文件大小（字节）
        
    Returns:
        上传进度信息字典
    """
    # 根据文件大小估算上传时间
    if file_size < 1024 * 1024:  # < 1MB
        estimated_seconds = 5
        complexity = "简单"
    elif file_size < 10 * 1024 * 1024:  # < 10MB
        estimated_seconds = 30
        complexity = "普通"
    elif file_size < 100 * 1024 * 1024:  # < 100MB
        estimated_seconds = 180
        complexity = "较大"
    else:
        estimated_seconds = 600
        complexity = "大文件"
    
    return {
        'file_size': file_size,
        'file_size_mb': round(file_size / 1024 / 1024, 2),
        'estimated_seconds': estimated_seconds,
        'estimated_minutes': round(estimated_seconds / 60, 1),
        'complexity': complexity
    }


# 当此脚本被直接运行时，调用main函数
if __name__ == "__main__":
    local_file_path = r'D:\文档\桌面\tesat\pdf\新扬.PDF'  # 替换为您要上传的本地文件路径
    up_local_file(local_file_path)
