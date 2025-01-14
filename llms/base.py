from abc import ABC, abstractmethod
class BaseAI(ABC):
    @abstractmethod
    async def get_response(self, prompt, user_input, history, temperature=0.3, max_tokens=2048, stream=False):
        pass

