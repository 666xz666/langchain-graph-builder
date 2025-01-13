from .gpt import *
from .qianfan import *

def get_chat_openai(model_name):
    if model_name == 'openai':
        return get_gpt_chatopenai()
    if model_name == 'qianfan':
        return get_qianfan_chatopenai()
    else:
        raise ValueError("Invalid model name")