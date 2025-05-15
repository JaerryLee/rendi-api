from fastapi import Cookie, HTTPException, Depends
from jose import jwt
from core.config import settings

async def get_current_user_from_ws(
    token: str = Cookie(None, alias="access_token")
) -> str:
    """
    WebSocket용 종속성:
    - 쿠키 access_token 에서 JWT를 꺼내고
    - 서명/만료 검증 → sub(구글 user_id) 를 리턴
    """
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")