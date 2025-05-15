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

from azure.cognitiveservices.speech import (
    SpeechConfig,
    SpeechRecognizer,
    AudioConfig,
    PropertyId
)
from azure.cognitiveservices.speech.transcription import ConversationTranscriber
from azure.cognitiveservices.speech.audio import PushAudioInputStream
import azure.cognitiveservices.speech as speechsdk

from core.config import settings
from core.database import engine, Base
from routers import auth, profile, survey, partner, checklist, schedules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure SpeechConfig
speech_config = SpeechConfig(
    subscription=settings.AZURE_SPEECH_KEY,
    endpoint=str(settings.AZURE_SPEECH_ENDPOINT)
)
speech_config.speech_recognition_language = "ko-KR"

speech_config.set_property(
    PropertyId.SpeechServiceResponse_DiarizeIntermediateResults,
    "true"
)
speech_config.set_service_property(
    "Speech_SegmentationSilenceTimeoutMs",
    "500",
    speechsdk.ServicePropertyChannel.UriQueryParameter
)
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
    loop = asyncio.get_running_loop()

    # 1) 스트림 및 Transcriber 생성
    push_stream = PushAudioInputStream()
    audio_input = AudioConfig(stream=push_stream)
    transcriber = ConversationTranscriber(speech_config, audio_input)

    # 2) 이벤트 콜백 등록
    def on_transcribing(evt):
        loop.create_task(websocket.send_json({
            "text": evt.result.text,
            "is_final": False,
            "speaker_id": evt.result.speaker_id,
            "timestamp": datetime.utcnow().isoformat()
        }))

    def on_transcribed(evt):
        loop.create_task(websocket.send_json({
            "text": evt.result.text,
            "is_final": True,
            "speaker_id": evt.result.speaker_id,
            "timestamp": datetime.utcnow().isoformat()
        }))

    transcriber.transcribing.connect(on_transcribing)
    transcriber.transcribed.connect(on_transcribed)

    # 3) 스트리밍 시작
    transcriber.start_transcribing_async()

    try:
        # 4) WebSocket → PushStream
        while True:
            chunk = await websocket.receive_bytes()
            push_stream.write(chunk)

    except WebSocketDisconnect:
        # 클라이언트가 stop 버튼을 누르거나 연결이 끊긴 경우
        logger.info("WebSocket disconnected by client")
        pass

    finally:
        # 5) 자원 정리 (한 번만)
        push_stream.close()
        transcriber.stop_transcribing_async()
        try:
            await websocket.close()
        except RuntimeError:
            # 이미 닫혔을 수 있으니 무시
            pass

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
