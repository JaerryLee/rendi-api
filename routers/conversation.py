from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict
from uuid import UUID

from schemas import (
    ConversationCreate,
    ConversationOut,
    MessageIn,
    RealTimeMemoryIn,
    RealTimeAnalysisOut,
    BreaktimeRecommendationIn,
    BreaktimeRecommendationOut,
    FinalReportIn,
    FinalReportOut,
)
from services.session_services import (
    create_conversation,
    add_message,
    get_realtime_memory,
    get_realtime_analysis,
    get_breaktime_recommendation,
    create_final_report,
)
from deps import get_current_user

router = APIRouter(
    prefix="/api/v1/conversation",
    tags=["conversation"],
)

@router.post("",
    response_model=ConversationOut,
    summary="새 대화 세션 생성"
)
async def post_conversation(
    payload: ConversationCreate
) -> ConversationOut:
    """
    새로운 conversation session 을 생성합니다.
    """
    raw = await create_conversation(payload.dict())
    return ConversationOut(**raw)

@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationOut,
    summary="메시지 전송 및 AI 응답 전체 반환",
)
async def post_message(
    conversation_id: UUID,
    payload: MessageIn
) -> ConversationOut:
    """
    대화에 메시지를 추가하고, 전체 AI 응답을 반환합니다.
    """
    raw = await add_message(conversation_id, payload.dict())
    if raw is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # role 치환: Guest-1 -> 나, 그 외 Guest-* -> 파트너
    msg: Dict[str, Any] = raw.get("message", {})
    orig = msg.get("role", "")
    if orig == "Guest-1":
        msg["role"] = "나"
    elif orig.startswith("Guest-"):
        msg["role"] = "파트너"
    # else: msg["role"] remains whatever AI server sent

    # 응답 envelope 구성
    return ConversationOut(
        message=msg,
        scores=raw.get("scores", {}),
        partner_memory=raw.get("partner_memory", {}),
        analysis=raw.get("analysis", {}),
        advice=raw.get("advice_recommendations", []),
        advice_metadatas=raw.get("advice_detail", {}),
        final_report=raw.get("final_report", ""),
    )

@router.post(
    "/{conversation_id}/realtime-memory",
    response_model=RealTimeMemoryIn,
    summary="실시간 메모리 업데이트",
)
async def realtime_memory(
    conversation_id: UUID,
    payload: RealTimeMemoryIn,
) -> RealTimeMemoryIn:
    """
    사용자 발화에 대한 실시간 메모리를 저장합니다.
    """
    memory = await get_realtime_memory(conversation_id, payload.dict())
    return RealTimeMemoryIn(extra_context=memory)

@router.get(
    "/{conversation_id}/realtime-analysis",
    response_model=RealTimeAnalysisOut,
    summary="실시간 분석 조회",
)
async def realtime_analysis(
    conversation_id: UUID
) -> RealTimeAnalysisOut:
    """
    현재 conversation 에 대한 실시간 분석 결과를 조회합니다.
    """
    scores = await get_realtime_analysis(conversation_id)
    return RealTimeAnalysisOut(analysis=scores)

@router.post(
    "/{conversation_id}/breaktime-advice/recommendation",
    response_model=BreaktimeRecommendationOut,
    summary="휴식 타임 추천",
)
async def breaktime_recommendation(
    conversation_id: UUID,
    payload: BreaktimeRecommendationIn,
) -> BreaktimeRecommendationOut:
    """
    중간 휴식에 대한 조언(추천)을 생성합니다.
    """
    advices = await get_breaktime_recommendation(conversation_id, payload.dict())
    return BreaktimeRecommendationOut(advice_recommendations=advices)

@router.post(
    "/{conversation_id}/final-report",
    response_model=FinalReportOut,
    summary="최종 보고서 생성",
)
async def final_report(
    conversation_id: UUID,
    payload: FinalReportIn,
) -> FinalReportOut:
    """
    대화 세션이 끝난 뒤 최종 보고서를 생성합니다.
    """
    report = await create_final_report(conversation_id, payload.dict())
    return FinalReportOut(final_report=report.get("final_report", ""))
