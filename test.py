import logging
from datetime import datetime
import os

os.makedirs('./log', exist_ok=True)
current_time = datetime.now().strftime('%Y%m%d-%H%M')
log_filename = f'./log/{current_time}上传文件.log'

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

for i in range(10):
    logging.info(f'Log entry {i + 1}')
    print(f'Log entry {i + 1} written to log file.')

if __name__ == '__main__':
    print("This is a test script.")
