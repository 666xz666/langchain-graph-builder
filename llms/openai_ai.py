from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from llms.base import BaseAI
import logging

class OpenAIAPI(BaseAI):
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL  # 如果需要指定基础URL，请确保它是有效的。
        )
        self.messages = []

    def initialize_conversation(self, system_prompt):
        """初始化对话，设置系统提示"""
        if not self.messages or self.messages[0]['role'] != "system":
            self.messages.insert(0, {"role": "system", "content": system_prompt})
            logging.info(f"Initialized conversation with system prompt: {system_prompt}")

    async def get_response(self, prompt, user_input, history=None, temperature=0.3, max_tokens=2048, stream=False):
        """
        获取来自OpenAI的响应。
        参数：
        - prompt: 系统提示内容
        - user_input: 用户输入的内容
        - history: 对话历史（可选）
        - temperature: 温度参数，默认值为0.3
        - max_tokens: 最大token数，默认值为2048
        - stream: 是否流式输出，默认为False
        返回：助手的响应文本
        """
        if history:
            self.messages.extend(history)
        self.messages.append({"role": "user", "content": user_input})
        self.initialize_conversation(prompt)  # 注意：这会每次都添加系统提示到消息列表中，可能不是你想要的行为。
        logging.info(f"User input: {user_input}")

        completion = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=self.messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        content_text = ""
        if stream:
            logging.info("OpenAI: (streaming)")
            for chunk in completion:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content is not None:
                    content_text += delta.content
                    logging.info(delta.content, extra={'streaming': True})
                    yield delta.content
            logging.info(f"OpenAI: {content_text}")
        else:
            content_text = completion.choices[0].message.content.strip()
            logging.info(f"OpenAI: {content_text}")
            yield content_text


if __name__ == "__main__":
    system_prompt = "你是通义，由阿里云开发的人工智能助手。"

    openai_api = OpenAIAPI()

    while True:
        user_input = input("用户: ")
        if user_input.lower() in ["退出", "exit"]:
            break
        response = openai_api.get_response(system_prompt, user_input, temperature=0.3, max_tokens=2048, stream=True)
        print("OpenAI:", response)