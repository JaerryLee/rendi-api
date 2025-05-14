from fastapi import APIRouter, Request, Depends, status, HTTPException, Cookie
from fastapi.responses import RedirectResponse, Response
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client.errors import MismatchingStateError
from jose import jwt
from datetime import datetime, timedelta

from core.config import settings
from core.database import get_session
from crud import get_user_by_google_id, create_user, get_profile
from schemas import TokenOut

router = APIRouter(prefix="/auth", tags=["Auth"])

# OAuth 클라이언트 등록
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# 프론트엔드 URL 설정
FRONTEND = str(settings.FRONTEND_URL).rstrip("/")
COOKIE_SECURE = True
COOKIE_SAMESITE = "none"


@router.get(
    "/google",
    response_class=RedirectResponse,
    summary="구글 OAuth 인증 시작"
)
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get(
    "/google/callback",
    response_class=RedirectResponse,
    summary="구글 OAuth 콜백"
)
async def callback(request: Request, db=Depends(get_session)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except MismatchingStateError:
        # state 불일치 시 홈으로 리다이렉트
        return RedirectResponse(FRONTEND, status_code=302)

    # 사용자 정보 조회
    user_info = await oauth.google.userinfo(token=token)
    google_id = user_info["sub"]

    # DB 조회/저장
    user = await get_user_by_google_id(db, google_id)
    if not user:
        user = await create_user(
            db,
            google_id,
            user_info["email"],
            user_info.get("name", ""),
            user_info.get("picture", "")
        )

    # JWT 생성
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_jwt = jwt.encode({"sub": google_id, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    refresh_jwt = jwt.encode({"sub": google_id}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # 프로필 존재 여부
    is_new = (await get_profile(db, user.id)) is None
    next_path = "sign-up" if is_new else ""
    redirect_url = f"{FRONTEND}/{next_path}" if next_path else FRONTEND

    # 쿠키 설정 후 리다이렉트
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        "access_token",
        access_jwt,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=".rendi.online",
        path="/"
    )
    response.set_cookie(
        "refresh_token",
        refresh_jwt,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=".rendi.online",
        path="/"
    )
    return response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="로그아웃"
)
async def logout():
    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp


@router.post(
    "/refresh",
    response_model=TokenOut,
    summary="토큰 재발급"
)
async def refresh_token(refresh_token: str = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        data = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_sub = data["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = jwt.encode(
        {"sub": user_sub, "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return {"access_token": new_access, "refresh_token": refresh_token}
