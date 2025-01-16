import json

import requests
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent
from config import NUMEXPR_MAX_THREADS
import logging
from utils import strip_tags
from config import MAX_INPUT_LENGTH

class SearchHelper:
    def __init__(self, region="wt-wt", time="d", max_results=5):
        """
        初始化SearchHelper类
        :param region: 搜索区域，默认为全球
        :param time: 搜索时间范围，默认为最近一天
        :param max_results: 最大结果数量，默认为5
        """
        self.wrapper = DuckDuckGoSearchAPIWrapper(region=region, time=time, max_results=max_results)
        self.search_run = DuckDuckGoSearchRun()
        self.search_results = DuckDuckGoSearchResults(api_wrapper=self.wrapper)

    def search_by_question(self, question):
        """
        根据问题返回指定结果
        :param question: 搜索问题
        :return: 搜索结果
        """
        result = self.search_run.invoke(question)
        return result

    def get_info_from_url(self, url_list):
        """
        多线程爬取URL页面内容
        :param url_list: URL列表
        :param max_workers: 最大线程数，默认为5
        :return: 页面内容列表
        """
        content_list = []

        def search_by_url(url):
            """
            通过URL获取页面内容
            :param url: 页面URL
            :return: 页面内容
            """
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            logging.info(f"正在爬取{url}...")
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # 如果请求失败，抛出HTTPError异常
                return response.text
            except Exception as e:
                return f"{url} 请求出错：{e}"

        with ThreadPoolExecutor(max_workers=NUMEXPR_MAX_THREADS) as executor:  # 创建线程池
            future_to_url = {executor.submit(search_by_url, url): url for url in url_list}  # 提交任务到线程池
            for future in as_completed(future_to_url):  # 获取任务结果
                url = future_to_url[future]
                content = future.result()  # 获取任务返回的结果
                striped_content = strip_tags(content)
                if "请求出错" in content:
                    logging.error(content)
                    content_list.append({"url": url, "content": None})
                else:
                    if len(striped_content) > MAX_INPUT_LENGTH:
                        logging.warning(
                            f"{url} 内容过长，长度为{len(striped_content)}，超过{MAX_INPUT_LENGTH}字符限制，取前{MAX_INPUT_LENGTH}字符"
                        )
                        content_list.append({"url": url, "content": striped_content[:MAX_INPUT_LENGTH]})
                    else:
                        content_list.append({"url": url, "content": striped_content})  # 将结果保存到列表中

        return content_list

    def search_detailed_results(self, query):
        """
        获取详细的搜索结果，包括链接和来源
        :param query: 搜索查询
        :return: 详细搜索结果
        """
        results = self.search_results.invoke(query)
        return results

# 示例用法
if __name__ == "__main__":
    search_helper = SearchHelper()

    # # 根据问题返回指定结果
    # question_result = search_helper.search_by_question("Python 列表推导式")
    # print("问题搜索结果：", question_result)

    # 通过URL获取页面内容
    url_list = ["https://www.python.org/", "https://www.google.com/", "https://www.bing.com/"]
    content_list = search_helper.get_info_from_url(url_list)
    print(content_list)

    # 获取详细的搜索结果
    # detailed_results = search_helper.search_detailed_results("DuckDuckGo API")
    # print("详细搜索结果：", detailed_results)