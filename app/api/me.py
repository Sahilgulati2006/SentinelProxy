from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.services.budget_service import BudgetService

router = APIRouter()
budget_service = BudgetService()


@router.get("/v1/me")
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    used_tokens = await budget_service.get_usage(current_user.user_id)

    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "api_key_prefix": current_user.api_key_prefix,
        "budget": {
            "monthly_token_limit": current_user.monthly_token_limit,
            "used_tokens": used_tokens,
            "remaining_tokens": max(
                current_user.monthly_token_limit - used_tokens,
                0,
            ),
        },
    }