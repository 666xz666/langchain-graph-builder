import requests
from config import *
import logging

def get_baike_explanation(words):
    """
    使用百度API获取词条的基础解释。

    :param words: 要查询的内容（例如：'苹果'）
    :return: API返回的解释内容或错误信息
    """
    # 请求地址
    url = "https://cn.apihz.cn/api/zici/baikebaidu.php"

    # 请求参数
    params = {
        'id': APIHZ_USER_ID,
        'key': APIHZ_USER_KEY,
        'words': words
    }

    # 发送GET请求
    response = requests.get(url, params=params)

    # 检查状态码
    if response.status_code == 200:
        # 解析JSON响应
        result = response.json()
        # 检查API返回的状态码
        if result['code'] == 200:
            return result['msg']  # 返回解释内容
        else:
            raise Exception(result['msg'])  # 抛出异常
    else:
        return "请求失败，状态码：{}".format(response.status_code)


def extract_keywords(words, separator = " "):
    """
    使用API提取指定文本的关键词。

    :param words: 要提取关键词的文本
    :param user_id: 用户中心的数字ID
    :param user_key: 用户中心通讯秘钥
    :param separator: 关键词之间的分隔符，默认为"|"
    :return: 关键词列表或错误信息
    """
    # 请求地址
    url = "https://cn.apihz.cn/api/zici/fenci.php"

    # 请求参数
    params = {
        'id': APIHZ_USER_ID,
        'key': APIHZ_USER_KEY,
        'type': separator,
        'words': words
    }

    # 发送GET请求
    response = requests.get(url, params=params)

    # 检查状态码
    if response.status_code == 200:
        # 解析JSON响应
        result = response.json()
        # 检查API返回的状态码
        if result['code'] == 200:
            # 返回关键词列表
            return result['msg'].split(separator)
        else:
            raise Exception(result['msg'])  # 抛出异常
    else:
        return "请求失败，状态码：{}".format(response.status_code)


if __name__ == '__main__':
    print(extract_keywords("苹果手机的价格是多少？"))
    print(get_baike_explanation("汽车"))