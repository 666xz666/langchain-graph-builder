from langchain_community.chat_models import QianfanChatEndpoint
import os
from config import QIANFAN_AK, QIANFAN_SK


def get_qianfan_chatopenai():
    os.environ["QIANFAN_AK"] = QIANFAN_AK
    os.environ["QIANFAN_SK"] = QIANFAN_SK
    llm = QianfanChatEndpoint(
        streaming=False,
    )
    return llm
