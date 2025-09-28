import logging
from datetime import datetime
from docx2pdf import convert


def word_to_pdf(input_path, output_path):
    convert(input_path, output_path)
    return output_path

if __name__ == '__main__':
    word_to_pdf('./test.doc', './test.pdf')
    print('转换成功')
