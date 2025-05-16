import httpx
from typing import Any, Dict, Optional
from uuid import UUID

from core.config import settings

BASE_URL = settings.AI_SERVER_URL.rstrip("/")

async def create_conversation(conversation_id: str, payload: dict):
    return (await client.post(f"{BASE_URL}/api/v1/conversation/{conversation_id}", json=payload)).json()
'''
async def create_conversation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    새 대화 세션을 생성합니다.
    POST /api/v1/conversation
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/api/v1/conversation", json=payload)
        resp.raise_for_status()
        return resp.json()
'''

async def add_message(conversation_id: UUID, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    대화에 메시지를 추가하고, AI의 전체 응답(Envelope)을 반환합니다.
    POST /api/v1/conversation/{conversation_id}/messages
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/conversation/{conversation_id}/messages",
            json=payload
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


async def get_realtime_memory(conversation_id: UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    실시간 메모리를 생성/조회합니다.
    POST /api/v1/conversation/{conversation_id}/realtime-memory
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/conversation/{conversation_id}/realtime-memory",
            json=payload
        )
        resp.raise_for_status()
        # 스펙에 따르면 키가 partner_memory
        return resp.json().get("partner_memory", {})


async def get_realtime_analysis(conversation_id: UUID) -> Dict[str, Any]:
    """
    실시간 분석 결과를 조회합니다.
    GET /api/v1/conversation/{conversation_id}/realtime-analysis
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/v1/conversation/{conversation_id}/realtime-analysis")
        resp.raise_for_status()
        # 스펙에 따르면 키가 scores
        return resp.json().get("scores", {})


async def get_breaktime_recommendation(conversation_id: UUID, payload: Dict[str, Any]) -> Any:
    """
    휴식 타임 추천을 생성합니다.
    POST /api/v1/conversation/{conversation_id}/breaktime-advice/recommendation
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/conversation/{conversation_id}/breaktime-advice/recommendation",
            json=payload
        )
        resp.raise_for_status()
        # 스펙에 따르면 키가 advice_metadatas
        return resp.json().get("advice_metadatas", [])


async def get_breaktime_advice_detail(conversation_id: UUID, advice_id: str) -> Dict[str, Any]:
    """
    추천된 조언의 상세 내용을 조회합니다.
    POST /api/v1/conversation/{conversation_id}/breaktime-advice/{advice_id}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/conversation/{conversation_id}/breaktime-advice/{advice_id}"
        )
        resp.raise_for_status()
        return resp.json()


async def create_final_report(conversation_id: UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 보고서를 생성합니다.
    POST /api/v1/conversation/{conversation_id}/final-report
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/conversation/{conversation_id}/final-report",
            json=payload
        )
        resp.raise_for_status()
        return resp.json()
