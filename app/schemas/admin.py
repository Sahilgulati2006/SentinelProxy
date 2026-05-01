from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CreateUserRequest(BaseModel):
    email: EmailStr
    monthly_token_limit: int = Field(default=100000, ge=1)


class UserResponse(BaseModel):
    id: str
    email: str
    monthly_token_limit: int
    is_active: bool
    created_at: datetime


class UpdateBudgetRequest(BaseModel):
    monthly_token_limit: int = Field(ge=1)


class CreateAPIKeyRequest(BaseModel):
    user_id: str
    name: str = "default"


class CreateAPIKeyResponse(BaseModel):
    id: str
    user_id: str
    key_prefix: str
    name: str
    is_active: bool
    api_key: str


class APIKeyResponse(BaseModel):
    id: str
    user_id: str
    key_prefix: str
    name: str
    is_active: bool
    created_at: datetime