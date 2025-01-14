import os
import logging
import datetime
from config import *
import logging.config
from langchain_core.documents import Document
from fastapi import UploadFile
import re
from bs4 import BeautifulSoup


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
            'file_uuid': item['file_uuid'],
            'kb_uuid': item['kb_uuid'],
        }
    )
    return document


async def save_upload_file(file: UploadFile, file_path: str):
    """
    将 FastAPI UploadFile 对象保存到指定路径。

    :param file: FastAPI UploadFile 对象
    :param file_path: 要保存文件的完整路径
    """
    # 确保目录存在，如果不存在则创建
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # 使用 with 语句确保文件正确关闭
    with open(file_path, "wb") as buffer:
        # 读取文件内容并写入到目标路径
        contents = await file.read()
        buffer.write(contents)


def extract_url(text) -> list[str]:
    """
    从文本中提取 URL。

    :param text: 文本内容
    :return: 文本中提取到的 URL 列表
    """
    regex = re.compile(
        r'(?:https?|ftp)://(?:\S+(?::\S*)?@)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25['
        r'0-5])){2}\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4])|(?:[a-z¡-￿0-9]+-?)*[a-z¡-￿0-9]+('
        r'?:\.(?:[a-z¡-￿0-9]+-?)*[a-z¡-￿0-9]+)*\.[a-z¡-￿]{2,})(?::\d{2,'
        r'5})?(?:/\S*)?',  # path
        re.IGNORECASE)
    return re.findall(regex, text)


def strip_tags(html):
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html, 'html.parser')

    # 移除所有<script>和<style>标签及其内容
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # 提取网页中的文本内容
    text = soup.get_text()

    # 替换所有回车和换行符为一个空格
    text = text.replace('\n', ' ').replace('\r', ' ')
    # 替换所有连续空格为一个空格
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空格
    text = text.strip()

    return text



if __name__ == '__main__':
    # file_path = r"D:\xz\大创\矿大智慧助手\代码\langchain-graph-builder\assets\README.MD"
    # print(get_file_name(file_path))
    text = """
    # langchain-graph-builder

    ## 项目简介
    
    langchain-graph-builder 是一个基于 FastAPI 
    构建的后端服务项目，旨在为知识库的创建、管理以及与之相关的对话功能提供接口支持。通过该项目，用户可以方便地创建知识库、上传文件至知识库、获取文件内容、删除知识库、生成知识库文件向量、获取知识库信息、进行大模型流式对话以及 
    RAG 对话等操作，同时还支持创建知识库图谱。
    
    ## 快速启动
    
    ### 1. 配置环境
    
    ```shell
    git clone https://github.com/666xz666/langchain-graph-builder.git
    cd langchain-graph-builder
    
    conda create -n lgb python=3.11 -y
    conda activate lgb
    
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```
    
    ### 2. 复制配置文件
    
    ```shell
    python config_tool.py --copy
    ```
    
    ### 3. 配置模型
    
    配置大模型api key
    
    embedding模型下载:
    
     https://pan.baidu.com/s/1XKQfFnSLbF0AjTLy_BCeFQ?pwd=fkrv 
    
    ### 4. 配置neo4j
    
    安装neo4j 5.21.0, 配置apoc
    
    https://blog.csdn.net/m0_63593482/article/details/133096869
    
    ### 5. 配置路径信息
    
    知识库存储目录，日志目录, 模型路径等
    
    ### 6. 启动app
    
    ```shell
    python app.py
    ```
    
    ## 文档
    
    启动后在`<host>:<port>/redoc`能查看文档
    
    ![fa48a08dea405ac3d0b043960cb1102](./assets/fa48a08dea405ac3d0b043960cb1102.png)
    
    ## Q&A
    
    ### 1.  “No module named pwd”（for Windows）
    
    https://blog.csdn.net/qq_40821260/article/details/137644996
    """
    print(extract_url(text))
