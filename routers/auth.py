from fastapi import APIRouter, Request, Response, Depends, status, HTTPException, Cookie
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from jose import jwt
from datetime import datetime, timedelta

from core.config import settings
from core.database import get_session
from crud import get_user_by_google_id, create_user
from schemas import TokenOut

router = APIRouter(prefix="/auth", tags=["Auth"])

# OAuth 클라이언트 등록 (메타데이터 자동 로드, userinfo() 지원)
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.get(
    "/google",
    summary="구글 OAuth 인증",
    description="프론트에서 이 API(`/auth/google`)로 호출해 주세요.",
    response_class=RedirectResponse
)
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get(
    "/google/callback",
    summary="구글 OAuth 인증 콜백",
    description="구글 로그인 후 이 API로 리다이렉트됩니다.",
    response_class=RedirectResponse,
    status_code=302,
)
async def callback(
    request: Request,
    # response: Response,
    db=Depends(get_session)
):
    # 토큰 교환
    token = await oauth.google.authorize_access_token(request)
    # ⇨ 변경: parse_id_token 대신 userinfo() 사용
    user_info = await oauth.google.userinfo(token=token)

    # DB에 사용자 존재 확인 및 저장
    google_id = user_info["sub"]
    user = await get_user_by_google_id(db, google_id)
    if not user:
        user = await create_user(
            db,
            google_id,
            user_info["email"],
            user_info.get("name", ""),
            user_info.get("picture", "")
        )

    # JWT 발급
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_jwt = jwt.encode(
        {"sub": google_id, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    refresh_jwt = jwt.encode({"sub": google_id}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # 쿠키 세팅 & JSON 반환
    frontend = settings.FRONTEND_URL  # .env 에 https://www.rendi.online 으로 설정되어 있어야 함
    response = RedirectResponse(url=frontend, status_code=302)
    response.set_cookie("access_token", access_jwt, httponly=True, secure=True, samesite="strict")
    response.set_cookie("refresh_token", refresh_jwt, httponly=True, secure=True, samesite="strict")
    return response


@router.post(
    "/logout",
    summary="로그아웃",
    description="Access/Refresh 토큰을 삭제합니다.",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response
)
async def logout():
    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp


@router.post(
    "/refresh",
    summary="JWT 토큰 재발급",
    description="Access 토큰이 만료되면 이 API(`/auth/refresh`)로 재발급 받으세요.",
    response_model=TokenOut
)
async def refresh_token(
    refresh_token: str = Cookie(None)
):
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
