from dotenv import load_dotenv
load_dotenv('.env')

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.utils import get_openapi
from google.cloud import speech

from core.config import settings
from core.database import engine, Base
from routers import auth, profile, survey, partner, checklist, schedules

app = FastAPI(
    title="Rendi API",
    version="1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# 1) SessionMiddleware가 먼저 설정되어야 세션 쿠키를 올바르게 읽고 씁니다.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=False,
)

# 2) CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# 디버그용 토큰 확인 엔드포인트
@app.get("/debug/token")
def debug_token(access_token: str = Cookie(None, alias="access_token")):
    return {"access_token": access_token}

# 로그인 페이지
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/login.html")

# DB 테이블 생성
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# WebSocket 음성 스트리밍 엔드포인트
@app.websocket("/ws/speech")
async def speech_ws(websocket: WebSocket):
    await websocket.accept()
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR",
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )

    async def request_generator():
        # 첫 요청: 설정 전송
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
        try:
            while True:
                chunk = await websocket.receive_bytes()
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
        except WebSocketDisconnect:
            return

    requests = request_generator()
    responses = client.streaming_recognize(requests=requests)

    try:
        for response in responses:
            for result in response.results:
                await websocket.send_json({
                    "text": result.alternatives[0].transcript,
                    "is_final": result.is_final,
                })
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(survey.router)
app.include_router(partner.router)
app.include_router(checklist.router)
app.include_router(schedules.router)


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
