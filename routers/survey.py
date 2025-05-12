from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from deps import get_current_user
from core.database import get_session
from schemas import (
    QuestionOut, QuestionList,
    ChoiceAnswerList, TextQuestionList,
    TextAnswerList, SaveResult
)
from crud import upsert_answers
from models import (
    LifestyleAnswer, TraitAnswer,
    PreferenceAnswer, ValuesAnswer,
    IntroductionAnswer
)

router = APIRouter(prefix="/survey", tags=["survey"])

# 화면에 맞춰 QUESTIONS 정의 (생략, 위 예시 참고)
QUESTION_BANK = {
    "lifestyle": [ ... ],
    "trait":     [ ... ],
    "preference":[ ... ],
    "values":    [ ... ],
}

INTRO_QUESTIONS = [ {"id":1,"prompt":"..."} , ... ]

@router.get("/{section}", response_model=QuestionList)
async def get_choices(section: str, user=Depends(get_current_user)):
    if section in QUESTION_BANK:
        return [QuestionOut(**q) for q in QUESTION_BANK[section]]
    raise HTTPException(404,"Unknown section")

@router.post("/{section}", response_model=SaveResult)
async def post_choices(
    section: str,
    payload: ChoiceAnswerList,
    user=Depends(get_current_user),
    db: AsyncSession=Depends(get_session)
):
    cls_map = {
        "lifestyle": LifestyleAnswer,
        "trait":     TraitAnswer,
        "preference":PreferenceAnswer,
        "values":    ValuesAnswer
    }
    if section not in cls_map:
        raise HTTPException(404,"Unknown section")
    saved = await upsert_answers(db, user.id, payload.answers, cls_map[section], is_text=False)
    return SaveResult(status="success", saved_count=saved)

@router.get("/introduction", response_model=TextQuestionList)
async def get_intro(user=Depends(get_current_user)):
    return INTRO_QUESTIONS

@router.post("/introduction", response_model=SaveResult)
async def post_intro(
    payload: TextAnswerList,
    user=Depends(get_current_user),
    db: AsyncSession=Depends(get_session)
):
    saved = await upsert_answers(db, user.id, payload.answers, IntroductionAnswer, is_text=True)
    return SaveResult(status="success", saved_count=saved)
