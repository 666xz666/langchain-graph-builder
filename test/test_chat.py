import requests
from config import *
import logging



# 处理流式响应
try:
    # 设置请求的 URL 和参数
    url = "http://" + SERVER_HOST + ":" + str(SERVER_PORT) + "/chat/chat"
    logging.info("url: " + url)
    headers = {"Content-Type": "application/json"}
    data = {
        "model_name": "kimi",
        "user_input": "介绍中国矿业大学",
        "stream": True
    }

    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=data, stream=True)

    # 解析 JSON 响应
    response_data = response.json()

    # 打印响应内容
    print("响应状态码:", response_data["code"])
    print("响应内容:", response_data["data"])
except Exception as e:
    print(f"Error: {e}")