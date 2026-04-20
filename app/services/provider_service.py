from app.core.config import settings
from app.providers.routers import get_provider
from app.schemas.chat import ChatCompletionRequest


class ProviderService:
    def __init__(self):
        self.provider = get_provider()
        self.provider_name = settings.PROVIDER_NAME

    async def forward(self, payload: ChatCompletionRequest) -> dict:
        return await self.provider.create_chat_completion(payload)