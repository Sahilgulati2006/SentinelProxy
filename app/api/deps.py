from fastapi import Depends

from app.core.security import verify_api_key


RequireAPIKey = Depends(verify_api_key)