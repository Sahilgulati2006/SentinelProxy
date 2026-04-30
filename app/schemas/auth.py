from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str
    api_key_prefix: str
    monthly_token_limit: int