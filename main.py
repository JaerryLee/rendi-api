# main.py
from dotenv import load_dotenv
load_dotenv(".env")

import json
import logging
import asyncio
from datetime import datetime

import grpc
import requests
import contextlib

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.utils import get_openapi
from jose import jwt

from clovaspeech.nest_pb2 import NestRequest, NestConfig, NestData, RequestType
from clovaspeech.nest_pb2_grpc import NestServiceStub

from core.config import settings
from core.database import engine, Base
from routers import auth, profile, survey, partner, checklist, schedules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Rendi API",
    version="1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# 세션, CORS, static 설정
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="none",
    https_only=True,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/login", include_in_schema=False)
async def login_page():
    return FileResponse("static/login.html")


@app.get("/ws_test", include_in_schema=False)
async def ws_test_page():
    return FileResponse("static/ws_test.html")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.websocket("/ws/speech")
async def speech_ws(websocket: WebSocket):
    await websocket.accept()
    
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=4401)
        
    channel = grpc.aio.secure_channel(
        settings.CLOVA_GRPC_URL,
        grpc.ssl_channel_credentials(),
    )
    stub = NestServiceStub(channel)
    
    cfg = {"transcription": {"language": "ko"}}
    cfg_msg = NestConfig(config=json.dumps(cfg))

    # 5) asyncio.Queue 로 오디오 청크 관리
    audio_q: asyncio.Queue[bytes] = asyncio.Queue()

    # 6) 요청 메시지 생성기
    async def request_generator():
        # 1) CONFIG 메시지
        yield NestRequest(
            type=RequestType.CONFIG,
            config=cfg_msg
        )

        # 2) AUDIO DATA 메시지
        while True:
            chunk = await audio_q.get()
            if chunk is None:
                break
            # extra_contents에 seqId, epFlag 포함
            extra = {"seqId": 0, "epFlag": False}
            yield NestRequest(
                type=RequestType.DATA,
                data=NestData(
                    chunk=chunk,
                    extra_contents=json.dumps(extra)
                )
            )

    # 7) gRPC streaming → WebSocket 전송
    async def grpc_stream():
        try:
            responses = stub.recognize(
                request_generator(),
                metadata=(("authorization", f"Bearer {settings.CLOVA_CLIENT_SECRET}"),),
            )
            async for resp in responses:
                # resp.contents 에는 문자열 텍스트
                await websocket.send_json({
                    "text": resp.contents,
                    "timestamp": datetime.utcnow().isoformat()
                })
        except grpc.aio.AioRpcError as e:
            logger.error("gRPC 스트리밍 중 오류", exc_info=e)
        finally:
            await channel.close()
            try:
                await websocket.close()
            except:
                pass

    # 8) Task 시작 및 WebSocket→Queue
    grpc_task = asyncio.create_task(grpc_stream())
    try:
        while True:
            try:
                # WebSocket이 살아 있는 동안에만 bytes를 받음
                data = await websocket.receive_bytes()
            except (WebSocketDisconnect, RuntimeError):
                # 클라이언트가 끊겼거나 이미 닫힌 소켓에 접근했을 때
                break

            # 정상적으로 data를 받았을 때만 큐에 넣음
            await audio_q.put(data)

    finally:
        # gRPC 스트림에 “종료” 신호 보냄
        await audio_q.put(None)
        # gRPC 태스크 취소 및 채널 닫기
        grpc_task.cancel()
        with contextlib.suppress(Exception):
            await channel.close()


# 나머지 라우터 포함
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
