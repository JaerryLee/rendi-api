# partner.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from deps import get_current_user
from core.database import get_session
from schemas import (
    QuestionOut,
    QuestionList,
    NewPartnerIn,
    PartnerOut,
    PartnerWithAnswersOut,
    PartnerListOut,
)
from crud import (
    create_partner_with_answers,
    get_latest_partner,
    get_all_partners,
    upsert_partner_answers,
)
router = APIRouter(prefix="/partners", tags=["partners"])
'''
PARTNER_QUESTIONS = [
    {
        "id": 1,,
        "type": "select",                  # 추가
        "title": "카카오톡 프로필 분위기",     # text → title
        "maxChoice": 1,                    # multiple=False → maxChoice=1
        "options": [
            {"label": "밝고 유쾌한 느낌(이모지/사진 활용)", "value": "1"},
            {"label": "깔끔하고 미니멀한 스타일",         "value": "2"},
            # …
        ],
    },
'''
PARTNER_QUESTIONS = [
    {
        "id": 1,
        "type": "select",
        "title": "카카오톡 프로필 분위기",
        "maxChoice": 1,
        "options": [
            {"label": "밝고 유쾌한 느낌(이모지/사진 활용)", "value": "1"},
            {"label": "깔끔하고 미니멀한 스타일",           "value": "2"},
            {"label": "감성적이거나 분위기 있는 이미지",    "value": "3"},
            {"label": "활동적인 느낌(여행/운동 사진 등)",    "value": "4"},
            {"label": "딱히 꾸미지 않음 or 비공개",         "value": "5"},
        ],
    },
    {
        "id": 2,
        "type": "select",
        "title": "첫 인사 톤",
        "maxChoice": 1,
        "options": [
            {"label": "말투가 부드럽고 공손한 편",     "value": "1"},
            {"label": "쿨하고 간단한 스타일",         "value": "2"},
            {"label": "다정하고 말 많은 편",          "value": "3"},
            {"label": "밍밍하지만 나쁘지 않은 느낌",   "value": "4"},
            {"label": "아직 판단하기 어려움",         "value": "5"},
        ],
    },
    {
        "id": 3,
        "type": "select",
        "title": "답장 템포",
        "maxChoice": 1,
        "options": [
            {"label": "답장이 빠르고 자주 와요",      "value": "1"},
            {"label": "일정한 간격으로 답해요",        "value": "2"},
            {"label": "느리지만 성의는 느껴져요",     "value": "3"},
            {"label": "느리고 건조한 느낌이에요",     "value": "4"},
            {"label": "아직 잘 모르겠어요",          "value": "5"},
        ],
    },
    {
        "id": 4,
        "type": "select",
        "title": "예상되는 직업 or 학과 이미지",
        "maxChoice": 1,
        "options": [
            {"label": "딱봐도 전문직 or 직무 강한 느낌", "value": "1"},
            {"label": "감성적이거나 예술계열 같음",      "value": "2"},
            {"label": "활발하고 사교적인 직군으로 보여요","value": "3"},
            {"label": "안정적이고 현실적인 느낌",        "value": "4"},
            {"label": "아직 잘 모르겠어요",            "value": "5"},
        ],
    },
    {
        "id": 5,
        "type": "select",
        "title": "대화 주도권 스타일",
        "maxChoice": 1,
        "options": [
            {"label": "주로 먼저 말을 걸어와요",        "value": "1"},
            {"label": "리액션 위주로 답해줘요",         "value": "2"},
            {"label": "질문을 잘 던지는 편이에요",       "value": "3"},
            {"label": "묻지 않으면 조용한 편이에요",     "value": "4"},
            {"label": "아직 잘 모르겠어요",            "value": "5"},
        ],
    },
]

@router.get(
    "/questions",
    response_model=QuestionList,
    summary="파트너 설문 질문 조회"
)
async def get_questions(user=Depends(get_current_user)):
    return PARTNER_QUESTIONS

@router.post(
    "",
    response_model=PartnerOut,
    status_code=status.HTTP_201_CREATED,
    summary="새 파트너 등록"
)
async def post_partner(
    payload: NewPartnerIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    partner = await upsert_partner_answers(db, user.id, payload.answers)
    return PartnerOut(id=partner.id)

@router.get(
    "",
    response_model=PartnerListOut,
    summary="파트너 조회"
)
async def list_partners(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    partners = await get_all_partners(db, user.id)
    return PartnerListOut(
        partners=[
            PartnerWithAnswersOut(
                id=p.id,
                answers=[
                    {"question_id": a.question_id, "option_id": a.option_id}
                    for a in p.answers
                ]
                ) for p in partners
        ]
    )

