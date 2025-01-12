from langchain_community.chat_models import ChatOpenAI
from config import *

def get_gpt_chatopenai():
    llm = ChatOpenAI(
        temperature=0,
        model=OPENAI_MODEL,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_BASE_URL
    )

    return llm