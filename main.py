from dotenv import load_dotenv
load_dotenv(".env")

import json
import asyncio
import contextlib
from datetime import datetime

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.utils import get_openapi
from jose import jwt

import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import PropertyId
from azure.cognitiveservices.speech.audio import PushAudioInputStream, AudioConfig
from azure.cognitiveservices.speech.transcription import ConversationTranscriber

from core.config import settings
from core.database import engine, Base
from routers import auth, profile, survey, partner, checklist, schedules, conversation
from deps import get_current_user

# logger
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rendi_api")

speech_config = speechsdk.SpeechConfig(
    subscription=settings.AZURE_SPEECH_KEY,
    region=settings.AZURE_SPEECH_REGION
)
speech_config.speech_recognition_language = "ko-KR"
speech_config.set_property(
    PropertyId.SpeechServiceResponse_DiarizeIntermediateResults, "true"
)
speech_config.set_service_property(
    "Speech_SegmentationSilenceTimeoutMs", "500",
    speechsdk.ServicePropertyChannel.UriQueryParameter
)

app = FastAPI(
    title="Rendi API",
    version="1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="none",
    https_only=True,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL], # "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# @app.get("/login", include_in_schema=False)
# async def login_page():
#     return FileResponse("static/login.html")

# @app.get("/ws_test", include_in_schema=False)
# async def ws_test_page():
#     return FileResponse("static/ws_test.html")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.websocket("/ws/speech")
async def speech_ws(
    websocket: WebSocket,
    user = Depends(get_current_user)
):
    await websocket.accept()
    session_cookies = websocket.cookies
    loop = asyncio.get_running_loop()

    # STT: Push stream setup
    push_stream = PushAudioInputStream()
    audio_input = AudioConfig(stream=push_stream)
    transcriber = ConversationTranscriber(speech_config, audio_input)

    def on_transcribed(evt):
        # only final recognized speech
        if evt.result.reason != speechsdk.ResultReason.RecognizedSpeech:
            return
        speaker = evt.result.speaker_id or "Guest-1"
        if speaker == "Guest-1":
            role_label = "나"
        else:
            role_label = "파트너"
        message_payload = {
            "message": {
                "message_id": datetime.utcnow().isoformat(),
                "role": role_label,
                "content": evt.result.text,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        loop.create_task(handle_ai_pipeline(websocket, message_payload, session_cookies))
    
    transcriber.transcribed.connect(on_transcribed)
    transcriber.start_transcribing_async()

    try:
        while True:
            data = await websocket.receive_bytes()
            push_stream.write(data)
    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", user.id)
    finally:
        push_stream.close()
        transcriber.stop_transcribing_async()
        with contextlib.suppress(RuntimeError):
            await websocket.close()
'''
async def safe_send(ws: WebSocket, data: dict):
    try:
        await ws.send_json(data)
    except RuntimeError:
        # 이미 close된 상태라면 무시
        logging.info("WebSocket already closed; cannot send message.")
'''        
async def handle_ai_pipeline(
    ws: WebSocket,
    payload: dict,
    session_cookies: dict
):
    base = settings.AI_SERVER_URL.rstrip("/")
    envelope = {}
    try:
        async with httpx.AsyncClient(cookies=session_cookies) as client:
            # 1) 대화 생성
            import uuid
            conv_id = str(uuid.uuid4())
            init = await client.post(f"{base}/api/v1/conversation/{conv_id}", json={})
            init.raise_for_status()

            # 2) 메시지 전송
            msg = await client.post(
                f"{base}/api/v1/conversation/{conv_id}/messages",
                json=payload
            )
            msg.raise_for_status()
            envelope.update(msg.json())

            # 3) 실시간 메모리
            mem = await client.post(
                f"{base}/api/v1/conversation/{conv_id}/realtime-memory", json={}
            )
            mem.raise_for_status()
            envelope['partner_memory'] = mem.json().get('partner_memory', {})

            # 4) 실시간 분석
            ana = await client.get(f"{base}/api/v1/conversation/{conv_id}/realtime-analysis")
            ana.raise_for_status()
            envelope['analysis'] = ana.json().get('scores', {})

            # 5) 조언 추천
            rec = await client.post(
                f"{base}/api/v1/conversation/{conv_id}/breaktime-advice/recommendation"
            )
            rec.raise_for_status()
            advice_list = rec.json().get('advice_metadatas', [])
            envelope['advice_metadatas'] = advice_list

            # 6) 조언 상세
            if advice_list:
                aid = advice_list[0]['advice_id']
                det = await client.post(
                    f"{base}/api/v1/conversation/{conv_id}/breaktime-advice/{aid}"
                )
                det.raise_for_status()
                envelope['advice_detail'] = det.json()

            # 7) 최종 보고서
            fin = await client.post(
                f"{base}/api/v1/conversation/{conv_id}/final-report", json={}
            )
            fin.raise_for_status()
            envelope['final_report'] = fin.json().get('final_report', '')
    except Exception as e:
        logger.error("AI pipeline error: %s", e)
        await ws.send_json({"error": str(e)})
        return
    # envelope['message'] = payload['message']
    # await safe_send(ws, envelope)
    envelope['message'] = payload['message']
    await ws.send_json(envelope)

# 라우터
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(survey.router)
app.include_router(partner.router)
app.include_router(checklist.router)
app.include_router(schedules.router)
app.include_router(conversation.router)

# OpenAPI
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