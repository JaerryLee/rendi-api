from fastapi import Cookie, Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.database import get_session
from crud import get_user_by_google_id

async def get_current_user(
    access_token: str = Cookie(None, alias="access_token"),
    db: AsyncSession = Depends(get_session)
):
    if not access_token:
        raise HTTPException(401, "Not authenticated")
    try:
        data = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        google_id = data.get("sub")
    except JWTError:
        raise HTTPException(401, "Invalid token")
    user = await get_user_by_google_id(db, google_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
