from .kimi import KimiAI
from .openai_ai import OpenAIAPI

def get_llm(model_name):
    if model_name == "kimi":
        return KimiAI()
    elif model_name == "openai":
        return OpenAIAPI()
    else:
        raise Exception("Unknown model name")