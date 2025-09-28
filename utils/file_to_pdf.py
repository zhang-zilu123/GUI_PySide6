"""
文件转PDF工具模块
提供各种文档格式转PDF的功能
"""
import os
import logging
from typing import Optional

# 设置日志
logger = logging.getLogger(__name__)

try:
    from docx2pdf import convert as docx2pdf_convert
except ImportError as e:
    logger.error(f"导入docx2pdf失败: {e}")
    docx2pdf_convert = None

try:
    import pypandoc
except ImportError as e:
    logger.error(f"导入pypandoc失败: {e}")
    pypandoc = None

try:
    from spire.xls import Workbook, FileFormat
except ImportError as e:
    logger.error(f"导入spire.xls失败: {e}")
    Workbook = None
    FileFormat = None


def excel_to_pdf(excel_path: str, output_dir: str) -> str:
    """Excel文件转PDF
    
    Args:
        excel_path: Excel文件路径
        output_dir: 输出目录
        
    Returns:
        生成的PDF文件路径
        
    Raises:
        FileNotFoundError: 输入文件不存在
        ValueError: 参数无效
        RuntimeError: 转换失败
    """
    try:
        # 参数验证
        if not excel_path or not isinstance(excel_path, str):
            raise ValueError("Excel文件路径无效")
        
        if not output_dir or not isinstance(output_dir, str):
            raise ValueError("输出目录路径无效")
            
        # 检查输入文件
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel文件不存在: {excel_path}")
            
        if not os.path.isfile(excel_path):
            raise ValueError(f"路径不是文件: {excel_path}")
            
        # 检查文件大小
        file_size = os.path.getsize(excel_path)
        if file_size == 0:
            raise ValueError("Excel文件为空")
        elif file_size > 100 * 1024 * 1024:  # 100MB限制
            raise ValueError(f"Excel文件太大 ({file_size / 1024 / 1024:.1f}MB)，超过100MB限制")
            
        # 检查依赖
        if Workbook is None or FileFormat is None:
            raise RuntimeError("Spire.XLS库未正确安装，无法进行Excel转PDF")
            
        # 创建输出目录
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"创建输出目录失败: {e}")
            
        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(excel_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        # 执行转换
        workbook = None
        try:
            workbook = Workbook()
            workbook.LoadFromFile(excel_path)
            workbook.SaveToFile(output_path, FileFormat.PDF)
            
            # 验证输出文件
            if not os.path.exists(output_path):
                raise RuntimeError("PDF文件未生成")
            elif os.path.getsize(output_path) == 0:
                raise RuntimeError("生成的PDF文件为空")
                
            logger.info(f"Excel转PDF成功: {excel_path} -> {output_path}")
            return output_path
            
        finally:
            if workbook:
                try:
                    workbook.Dispose()
                except Exception as e:
                    logger.warning(f"释放workbook资源失败: {e}")
                    
    except Exception as e:
        error_msg = f"Excel转PDF失败 {excel_path}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def docx_to_pdf(input_path: str, output_path: str) -> str:
    """Word文档转PDF
    
    Args:
        input_path: 输入Word文档路径
        output_path: 输出PDF文件路径
        
    Returns:
        生成的PDF文件路径
        
    Raises:
        FileNotFoundError: 输入文件不存在
        ValueError: 参数无效
        RuntimeError: 转换失败
    """
    try:
        # 参数验证
        if not input_path or not isinstance(input_path, str):
            raise ValueError("输入文件路径无效")
        
        if not output_path or not isinstance(output_path, str):
            raise ValueError("输出文件路径无效")
            
        # 检查输入文件
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Word文档不存在: {input_path}")
            
        if not os.path.isfile(input_path):
            raise ValueError(f"路径不是文件: {input_path}")
            
        # 检查文件大小
        file_size = os.path.getsize(input_path)
        if file_size == 0:
            raise ValueError("Word文档为空")
        elif file_size > 50 * 1024 * 1024:  # 50MB限制
            raise ValueError(f"Word文档太大 ({file_size / 1024 / 1024:.1f}MB)，超过50MB限制")
            
        # 检查依赖
        if docx2pdf_convert is None:
            raise RuntimeError("docx2pdf库未正确安装，无法进行Word转PDF")
            
        # 创建输出目录
        output_dir = os.path.dirname(output_path)
        if output_dir:
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                raise RuntimeError(f"创建输出目录失败: {e}")
                
        # 执行转换
        try:
            docx2pdf_convert(input_path, output_path)
            
            # 验证输出文件
            if not os.path.exists(output_path):
                raise RuntimeError("PDF文件未生成")
            elif os.path.getsize(output_path) == 0:
                raise RuntimeError("生成的PDF文件为空")
                
            logger.info(f"Word转PDF成功: {input_path} -> {output_path}")
            return output_path
            
        except Exception as convert_error:
            # 清理可能生成的空文件
            if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
                try:
                    os.remove(output_path)
                except:
                    pass
            raise convert_error
            
    except Exception as e:
        error_msg = f"Word转PDF失败 {input_path}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def rtf_to_pdf(input_path: str, output_path: str) -> str:
    """RTF文档转PDF
    
    Args:
        input_path: 输入RTF文档路径
        output_path: 输出PDF文件路径
        
    Returns:
        生成的PDF文件路径
        
    Raises:
        FileNotFoundError: 输入文件不存在
        ValueError: 参数无效
        RuntimeError: 转换失败
    """
    temp_docx_file = None
    try:
        # 参数验证
        if not input_path or not isinstance(input_path, str):
            raise ValueError("输入文件路径无效")
        
        if not output_path or not isinstance(output_path, str):
            raise ValueError("输出文件路径无效")
            
        # 检查输入文件
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"RTF文档不存在: {input_path}")
            
        if not os.path.isfile(input_path):
            raise ValueError(f"路径不是文件: {input_path}")
            
        # 检查文件大小
        file_size = os.path.getsize(input_path)
        if file_size == 0:
            raise ValueError("RTF文档为空")
        elif file_size > 50 * 1024 * 1024:  # 50MB限制
            raise ValueError(f"RTF文档太大 ({file_size / 1024 / 1024:.1f}MB)，超过50MB限制")
            
        # 检查依赖
        if pypandoc is None:
            raise RuntimeError("pypandoc库未正确安装，无法进行RTF转换")
        if docx2pdf_convert is None:
            raise RuntimeError("docx2pdf库未正确安装，无法进行最终PDF转换")
            
        # 创建输出目录
        output_dir = os.path.dirname(output_path)
        if output_dir:
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                raise RuntimeError(f"创建输出目录失败: {e}")
                
        # 生成临时docx文件路径
        temp_docx_file = input_path.replace('.rtf', '_temp.docx')
        
        try:
            # 第一步：RTF转DOCX
            pypandoc.convert_file(
                input_path,
                'docx',
                outputfile=temp_docx_file,
                extra_args=['--standalone']
            )
            
            # 验证临时文件
            if not os.path.exists(temp_docx_file):
                raise RuntimeError("RTF转DOCX失败，临时文件未生成")
            elif os.path.getsize(temp_docx_file) == 0:
                raise RuntimeError("RTF转DOCX失败，临时文件为空")
                
            # 第二步：DOCX转PDF
            docx2pdf_convert(temp_docx_file, output_path)
            
            # 验证输出文件
            if not os.path.exists(output_path):
                raise RuntimeError("PDF文件未生成")
            elif os.path.getsize(output_path) == 0:
                raise RuntimeError("生成的PDF文件为空")
                
            logger.info(f"RTF转PDF成功: {input_path} -> {output_path}")
            return output_path
            
        finally:
            # 清理临时文件
            if temp_docx_file and os.path.exists(temp_docx_file):
                try:
                    os.remove(temp_docx_file)
                    logger.info(f"已清理临时文件: {temp_docx_file}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {cleanup_error}")
                    
    except Exception as e:
        error_msg = f"RTF转PDF失败 {input_path}: {str(e)}"
        logger.error(error_msg)
        
        # 清理可能生成的文件
        for cleanup_file in [temp_docx_file, output_path]:
            if cleanup_file and os.path.exists(cleanup_file):
                try:
                    if os.path.getsize(cleanup_file) == 0:  # 只删除空文件
                        os.remove(cleanup_file)
                except:
                    pass
                    
        raise RuntimeError(error_msg) from e


def check_conversion_dependencies() -> dict:
    """检查转换依赖库的可用性
    
    Returns:
        依赖库状态字典
    """
    status = {
        'docx2pdf': docx2pdf_convert is not None,
        'pypandoc': pypandoc is not None,
        'spire_xls': Workbook is not None and FileFormat is not None,
    }
    
    missing = [name for name, available in status.items() if not available]
    status['all_available'] = len(missing) == 0
    status['missing'] = missing
    
    return status


if __name__ == '__main__':
    rtf_to_pdf('../test.rtf', '../test_rtf.pdf')
