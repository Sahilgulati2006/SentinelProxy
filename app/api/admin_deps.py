from fastapi import Depends

from app.core.admin_security import verify_admin_key


RequireAdminKey = Depends(verify_admin_key)