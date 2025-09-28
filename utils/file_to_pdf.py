import os
from docx2pdf import convert
import pypandoc
import comtypes.client

from spire.xls import *


def excel_to_pdf(excel_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(excel_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.pdf")
    workbook = Workbook()
    workbook.LoadFromFile(excel_path)
    workbook.SaveToFile(output_path, FileFormat.PDF)
    workbook.Dispose()
    return output_path


def docx_to_pdf(input_path, output_path):
    convert(input_path, output_path)
    return output_path


def rtf_to_pdf(input_path, output_path):
    docx_file = input_path.replace('.rtf', '.docx')
    pypandoc.convert_file(
        input_path,
        'docx',
        outputfile=docx_file,
        extra_args=['--standalone']
    )
    convert(docx_file, output_path)
    return output_path


if __name__ == '__main__':
    excel_to_pdf('../test.xls', '../test_excel.pdf')
