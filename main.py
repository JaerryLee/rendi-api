# main.py

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from core.config import settings
from core.database import engine, Base
from routers import auth, profile, survey, partner, dashboard

app = FastAPI(
    title="Rendi API",
    version="1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# 세션 미들웨어
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# 루트는 로그인 페이지로
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/login.html")

# 앱 기동 시 DB 테이블 생성
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 각 라우터 등록
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(survey.router)
app.include_router(partner.router)
app.include_router(dashboard.router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="Rendi Complete API Docs",
        routes=app.routes,
    )

    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["cookieAuth"] = {
        "type": "apiKey",
        "in": "cookie",
        "name": "access_token"
    }

    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            operation.setdefault("security", []).append({"cookieAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
