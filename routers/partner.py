# partner.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from deps import get_current_user
from core.database import get_session
from schemas import (
    QuestionOut,
    QuestionList,
    NewPartnerIn,
    PartnerListOut,
    PartnerOut, 
    PartnerWithAnswersOut,
    ScheduleIn
)
from crud import create_partner_with_answers, get_latest_partner, get_all_partners

router = APIRouter(prefix="/partners", tags=["partners"])

PARTNER_QUESTIONS = [
    {
        "id": 1,
        "text": "카카오톡 프로필 분위기",
        "multiple": False,
        "options": [
            {"id": "1", "text": "밝고 유쾌한 느낌(이모지/사진 활용)"},
            {"id": "2", "text": "깔끔하고 미니멀한 스타일"},
            {"id": "3", "text": "감성적이거나 분위기 있는 이미지"},
            {"id": "4", "text": "활동적인 느낌(여행/운동 사진 등)"},
            {"id": "5", "text": "딱히 꾸미지 않음 or 비공개"},
        ],
    },
    {
        "id": 2,
        "text": "첫 인사 톤",
        "multiple": False,
        "options": [
            {"id": "1", "text": "말투가 부드럽고 공손한 편"},
            {"id": "2", "text": "쿨하고 간단한 스타일"},
            {"id": "3", "text": "다정하고 말 많은 편"},
            {"id": "4", "text": "밍밍하지만 나쁘지 않은 느낌"},
            {"id": "5", "text": "아직 판단하기 어려움"},
        ],
    },{
        "id": 3,
        "text": "답장 템포",
        "multiple": False,
        "options": [
            {"id": "1", "text": "답장이 빠르고 자주 와요"},
            {"id": "2", "text": "일정한 간격으로 답해요"},
            {"id": "3", "text": "느리지만 성의는 느껴져요"},
            {"id": "4", "text": "느리고 건조한 느낌이에요"},
            {"id": "5", "text": "아직 잘 모르겠어요"},
        ],
    },{
        "id": 4,
        "text": "예상되는 직업 or 학과 이미지",
        "multiple": False,
        "options": [
            {"id": "1", "text": "딱봐도 전문직 or 직무 강한 느낌"},
            {"id": "2", "text": "감성적이거나 예술계열 같음"},
            {"id": "3", "text": "활발하고 사교적인 직군으로 보여요"},
            {"id": "4", "text": "안정적이고 현실적인 느낌"},
            {"id": "5", "text": "아직 잘 모르겠어요"},
        ],
    },{
        "id": 5,
        "text": "대화 주도권 스타일",
        "multiple": False,
        "options": [
            {"id": "1", "text": "주로 먼저 말을 걸어와요"},
            {"id": "2", "text": "리액션 위주로 답해줘요"},
            {"id": "3", "text": "질문을 잘 던지는 편이에요"},
            {"id": "4", "text": "묻지 않으면 조용한 편이에요"},
            {"id": "5", "text": "아직 잘 모르겠어요"},
        ],
    },
]
@router.get("/questions", response_model=QuestionList)
async def get_questions(user=Depends(get_current_user)):
    return [QuestionOut(**q) for q in PARTNER_QUESTIONS]

@router.post("", response_model=PartnerOut, status_code=status.HTTP_201_CREATED)
async def post_partner(
    payload: NewPartnerIn,
    user=Depends(get_current_user),
    db: AsyncSession=Depends(get_session)
):
    p = await create_partner_with_answers(db, user.id, payload.meeting_date, payload.answers)
    return p

@router.get("/latest", response_model=PartnerWithAnswersOut, summary="마지막 등록된 파트너 조회")
async def get_latest(user=Depends(get_current_user), db=Depends(get_session)):
    p = await get_latest_partner(db, user.id)
    if not p:
        raise HTTPException(status_code=404, detail="No partner registered")
    return PartnerWithAnswersOut(
        id=p.id,
        meeting_date=p.meeting_date,
        answers=[{"question_id": a.question_id, "option_id": a.option_id} for a in p.answers]
    )
@router.get("", response_model=PartnerListOut, summary="내가 등록한 모든 파트너 조회")
async def list_partners(user=Depends(get_current_user), db=Depends(get_session)):
    partners = await get_all_partners(db, user.id)
    return PartnerListOut(
        partners=[
            PartnerWithAnswersOut(
                id=p.id,
                meeting_date=p.meeting_date,
                answers=[{"question_id": a.question_id, "option_id": a.option_id} for a in p.answers]
            )
            for p in partners
        ]
    )
    
@router.post(
    "/schedule",
    response_model=PartnerOut,
    summary="마지막 파트너에 대한 소팅(날짜/시간/장소) 저장"
)
async def schedule_partner(
    payload: ScheduleIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    - 사용자가 마지막으로 등록한 파트너의
      date/time/place를 업데이트합니다.
    - 파트너를 하나도 등록하지 않았으면 404 반환.
    """
    try:
        partner = await update_latest_partner_schedule(
            db,
            user.id,
            payload.meeting_date,
            payload.meeting_time,
            payload.meeting_place
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="등록된 파트너가 없습니다.")
    return partner