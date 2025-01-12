import os
import logging
import datetime
from config import *
import logging.config
from langchain_core.documents import Document

def get_file_name(file_path):
    if os.path.isfile(file_path):
        return os.path.splitext(os.path.basename(file_path))[0]
    else:
        return None

def get_logging():
    # 创建日志目录
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)

    # 设置日志文件路径
    log_file_path = os.path.join(LOG_PATH, datetime.datetime.now().strftime('%Y-%m-%d') + '.log')
    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # 创建文件处理器，并设置格式
    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)

    # 创建控制台处理器，并设置格式
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # 获取根日志记录器，并设置级别
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # 移除所有旧的处理器
    logger.handlers = []

    # 添加新的处理器
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # 记录一条初始化日志
    logger.info("日志系统初始化完成")
    return logger


def create_document_from_item(item):
    """
    从提供的数据项创建并返回一个Document对象。

    参数:
    item (dict): 包含文档信息的字典。

    返回:
    Document: 根据提供的数据项创建的文档对象。
    """
    document = Document(
        id=item['id'],
        page_content=item['text'],
        metadata={
            'embedding': item['embedding'],
            'source_filename': item['source_filename'],
            'source_url': item['source_url']
        }
    )
    return document

if __name__ == '__main__':
    file_path = r"D:\xz\大创\矿大智慧助手\代码\langchain-graph-builder\assets\README.MD"
    print(get_file_name(file_path))