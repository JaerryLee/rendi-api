# app/routers/survey.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from deps import get_current_user
from core.database import get_session
from crud import upsert_answers, get_user_answers
from schemas import ChoiceAnswerList, SaveResult, TextAnswerIn, QuestionWithAnswerOut
from models import (
    LifestyleAnswer,
    TraitAnswer,
    PreferenceAnswer,
    ValuesAnswer,
    IntroductionAnswer
)
from constants import QUESTION_DEFINITIONS


router = APIRouter(prefix="/survey", tags=["survey"])


@router.get(
    "/lifestyle",
    response_model=List[QuestionWithAnswerOut],
    summary="Get Lifestyle with answers"
)
async def get_lifestyle(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    questions = [q for q in QUESTION_DEFINITIONS if 1 <= q["id"] <= 7]
    answers = await get_user_answers(db, user.id, LifestyleAnswer)
    out: List[QuestionWithAnswerOut] = []
    for q in questions:
        ans = answers.get(q["id"], [])
        out.append(QuestionWithAnswerOut(
            **q,
            answer_id=ans[0] if len(ans) == 1 else None,
            answer_ids=ans if len(ans) > 1 else None
        ))
    return out


@router.post(
    "/lifestyle",
    response_model=SaveResult,
    summary="Post Lifestyle"
)
async def post_lifestyle(
    payload: ChoiceAnswerList,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    saved = await upsert_answers(db, user.id, payload.answers, LifestyleAnswer, is_text=False)
    return SaveResult(status="success", saved_count=saved)


@router.get(
    "/identify",
    response_model=List[QuestionWithAnswerOut],
    summary="Get Identify with answers"
)
async def get_identify(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    questions = [q for q in QUESTION_DEFINITIONS if 8 <= q["id"] <= 20]
    answers = await get_user_answers(db, user.id, TraitAnswer)
    out: List[QuestionWithAnswerOut] = []
    for q in questions:
        ans = answers.get(q["id"], [])
        out.append(QuestionWithAnswerOut(
            **q,
            answer_id=ans[0] if len(ans) == 1 else None,
            answer_ids=ans if len(ans) > 1 else None
        ))
    return out


@router.post(
    "/identify",
    response_model=SaveResult,
    summary="Post Identify"
)
async def post_identify(
    payload: ChoiceAnswerList,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    saved = await upsert_answers(db, user.id, payload.answers, TraitAnswer, is_text=False)
    return SaveResult(status="success", saved_count=saved)


@router.get(
    "/preference",
    response_model=List[QuestionWithAnswerOut],
    summary="Get Preference with answers"
)
async def get_preference(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    questions = [q for q in QUESTION_DEFINITIONS if 21 <= q["id"] <= 27]
    answers = await get_user_answers(db, user.id, PreferenceAnswer)
    out: List[QuestionWithAnswerOut] = []
    for q in questions:
        ans = answers.get(q["id"], [])
        out.append(QuestionWithAnswerOut(
            **q,
            answer_id=ans[0] if len(ans) == 1 else None,
            answer_ids=ans if len(ans) > 1 else None
        ))
    return out


@router.post(
    "/preference",
    response_model=SaveResult,
    summary="Post Preference"
)
async def post_preference(
    payload: ChoiceAnswerList,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    saved = await upsert_answers(db, user.id, payload.answers, PreferenceAnswer, is_text=False)
    return SaveResult(status="success", saved_count=saved)


@router.get(
    "/beliefs",
    response_model=List[QuestionWithAnswerOut],
    summary="Get Beliefs with answers"
)
async def get_beliefs(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    questions = [q for q in QUESTION_DEFINITIONS if 28 <= q["id"] <= 33]
    answers = await get_user_answers(db, user.id, ValuesAnswer)
    out: List[QuestionWithAnswerOut] = []
    for q in questions:
        ans = answers.get(q["id"], [])
        out.append(QuestionWithAnswerOut(
            **q,
            answer_id=ans[0] if len(ans) == 1 else None,
            answer_ids=ans if len(ans) > 1 else None
        ))
    return out


@router.post(
    "/beliefs",
    response_model=SaveResult,
    summary="Post Beliefs"
)
async def post_beliefs(
    payload: ChoiceAnswerList,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    saved = await upsert_answers(db, user.id, payload.answers, ValuesAnswer, is_text=False)
    return SaveResult(status="success", saved_count=saved)


@router.post(
    "/essay",
    response_model=SaveResult,
    status_code=status.HTTP_201_CREATED,
    summary="Post Essay"
)
async def post_essay(
    payload: TextAnswerIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    saved = await upsert_answers(db, user.id, [payload], IntroductionAnswer, is_text=True)
    return SaveResult(status="success", saved_count=saved)