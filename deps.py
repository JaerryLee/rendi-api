from fastapi import Cookie, Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_session
from crud import get_user_by_google_id

async def get_current_user(
    access_token: str = Cookie(None),                   # 쿠키 이름을 access_token으로 바로 매핑
    db: AsyncSession = Depends(get_session)
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        google_id = payload.get("sub")
        if not google_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_google_id(db, google_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
