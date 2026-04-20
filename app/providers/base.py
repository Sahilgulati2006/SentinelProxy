from abc import ABC, abstractmethod
from app.schemas.chat import ChatCompletionRequest


class BaseProvider(ABC):
    @abstractmethod
    async def create_chat_completion(self, payload: ChatCompletionRequest) -> dict:
        raise NotImplementedError