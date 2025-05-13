# main.py

from fastapi import FastAPI, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.utils import get_openapi

from core.config import settings
from core.database import engine, Base
from routers import auth, profile, survey, partner, dashboard, checklist

app = FastAPI(
    title="Rendi API",
    version="1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# 1) SessionMiddleware 가 먼저 와야 세션 쿠키를 올바르게 읽고 씁니다.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",   # cross-site 케이스에서도 쿠키가 전송되도록
    https_only=False,    # HTTPS 환경에서만 작동 (운영 시 True)
)

# 2) 그 다음에 CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173",],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/debug/token")
def debug_token(access_token: str = Cookie(None, alias="access_token")):
    return {"access_token": access_token}

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/login.html")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 라우터 등록
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(survey.router)
app.include_router(partner.router)
app.include_router(dashboard.router)
app.include_router(checklist.router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description="Rendi API Docs",
        routes=app.routes,
    )
    comp = schema.setdefault("components", {})
    schemes = comp.setdefault("securitySchemes", {})
    schemes["cookieAuth"] = {"type": "apiKey", "in": "cookie", "name": "access_token"}
    for path in schema["paths"].values():
        for op in path.values():
            op.setdefault("security", []).append({"cookieAuth": []})
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
