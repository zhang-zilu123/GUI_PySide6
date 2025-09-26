import alibabacloud_oss_v2 as oss
import os


def up_local_file(local_file_path):
    # 配置API密钥
    os.environ["OSS_ACCESS_KEY_ID"] = ""
    os.environ["OSS_ACCESS_KEY_SECRET"] = ""

    # 从环境变量中加载凭证信息，用于身份验证
    credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()

    # 加载SDK的默认配置，并设置凭证提供者
    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider
    cfg.region = 'cn-shanghai'

    # 使用配置好的信息创建OSS客户端
    client = oss.Client(cfg)

    # 从本地文件路径中提取文件名
    file_name = os.path.basename(local_file_path)
    object_key = f"{'chatbot_25_0528/muai-models/cost_ident'}/{file_name}"

    # 以二进制读取模式打开文件，并上传
    with open(local_file_path, 'rb') as f:
        # 执行上传对象的请求，指定存储空间名称、对象名称和文件数据
        result = client.put_object(oss.PutObjectRequest(
            bucket='muai-models',
            key=object_key,
            body=f,
        ))

    # 检查上传是否成功
    if 200 <= result.status_code < 300:
        print('文件上传成功:', object_key, result)

    return object_key


# 当此脚本被直接运行时，调用main函数
if __name__ == "__main__":
    local_file_path = r'D:\文档\桌面\tesat\pdf\新扬.PDF'  # 替换为您要上传的本地文件路径
    up_local_file(local_file_path)
