from openai import OpenAI
from config import *
from .base import BaseAI
import logging

class KimiAI(BaseAI):
    def __init__(self):
        self.client = OpenAI(
            api_key=KIMI_API_KEY,
            base_url="https://api.moonshot.cn/v1"
        )
        self.messages = []

    def initialize_conversation(self, system_prompt):
        self.messages.append({"role": "system", "content": system_prompt})
        logging.info(f"Initialized conversation with system prompt: {system_prompt}")


    async def get_response(self, prompt, user_input, history=None, temperature=0.3, max_tokens=2048, stream=False):
        if not history or history != []:
            self.messages.extend(history)
        self.messages.append({"role": "user", "content": user_input})
        self.initialize_conversation(prompt)
        logging.info(f"User input: {user_input}")

        completion = self.client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=self.messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            content_text = ""
            logging.info("Kimi AI: (streaming)")
            for chunk in completion:
                delta = chunk.choices[0].delta
                if delta.content:
                    content_text += delta.content
                    logging.info(delta.content, extra={'streaming': True})
                    yield delta.content  # 直接yield每个数据块
            logging.info(f"Kimi AI: {content_text}")
        else:
            content_text = completion.choices[0].message.content
            logging.info(f"Kimi AI: {content_text}")
            yield content_text  # 对于非流式响应，一次性yield整个内容


if __name__ == "__main__":

    system_prompt = "你是 Kimi。"

    kimi_ai = KimiAI()

    while True:
        user_input = input("用户: ")
        if user_input.lower() in ["退出", "exit"]:
            break
        response = kimi_ai.get_response(system_prompt, user_input, temperature=0.3, max_tokens=2048, stream=True)
        print("Kimi AI:", response)
