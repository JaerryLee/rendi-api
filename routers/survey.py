from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from deps import get_current_user
from core.database import get_session
from crud import (
    upsert_answers,
    get_user_answers,
    get_group_input_answers,
    upsert_group_input_answers
)
from schemas import (
    ChoiceAnswerList,
    SaveResult,
    QuestionWithAnswerOut,
    GroupInputAnswerList,
    GroupInputOut,
    SubQuestionOut
)
from models import (
    LifestyleAnswer,
    TraitAnswer,
    PreferenceAnswer,
    ValuesAnswer,
    IntroductionAnswer,
    GroupInputAnswer
)
from constants import QUESTION_DEFINITIONS


router = APIRouter(prefix="/survey", tags=["survey"])

async def _load_and_merge(
    db: AsyncSession,
    user_id: int,
    qmin: int,
    qmax: int,
    model_cls,
    is_text: bool = False
) -> List[QuestionWithAnswerOut]:
    defs = [q for q in QUESTION_DEFINITIONS if qmin <= q["id"] <= qmax]
    stored = await get_user_answers(db, user_id, model_cls)
    out = []
    for q in defs:
        vals = stored.get(q["id"], [])
        out.append(QuestionWithAnswerOut(
            **q,
            answer_ids=vals or None,
            text=vals[0] if is_text and vals else None
        ))
    return out
@router.get(
    "/lifestyle",
    response_model=List[QuestionWithAnswerOut],
    summary="라이프스타일 설문"
)
async def get_lifestyle(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await _load_and_merge(db, user.id, 1, 7, LifestyleAnswer)


@router.post(
    "/lifestyle",
    response_model=SaveResult,
    summary="라이프스타일 설문"
)
async def post_lifestyle(payload: ChoiceAnswerList, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    cnt = await upsert_answers(db, user.id, payload.answers, LifestyleAnswer, is_text=False)
    return SaveResult(status="success", saved_count=cnt)


@router.get(
    "/identify",
    response_model=List[QuestionWithAnswerOut],
    summary="성향파악 설문"
)
async def get_identify(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await _load_and_merge(db, user.id, 8, 20, TraitAnswer)


@router.post(
    "/identify",
    response_model=SaveResult,
    summary="성향파악 설문"
)
async def post_identify(payload: ChoiceAnswerList, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    cnt = await upsert_answers(db, user.id, payload.answers, TraitAnswer, is_text=False)
    return SaveResult(status="success", saved_count=cnt)


@router.get(
    "/preference",
    response_model=List[QuestionWithAnswerOut],
    summary="취향파악 설문"
)
async def get_preference(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await _load_and_merge(db, user.id, 21, 27, PreferenceAnswer)


@router.post(
    "/preference",
    response_model=SaveResult,
    summary="취향파악 설문"
)
async def post_preference(payload: ChoiceAnswerList, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    cnt = await upsert_answers(db, user.id, payload.answers, PreferenceAnswer, is_text=False)
    return SaveResult(status="success", saved_count=cnt)


@router.get(
    "/beliefs",
    response_model=List[QuestionWithAnswerOut],
    summary="가치관파악 설문"
)
async def get_beliefs(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await _load_and_merge(db, user.id, 28, 33, ValuesAnswer)


@router.post(
    "/beliefs",
    response_model=SaveResult,
    summary="가치관파악 설문"
)
async def post_beliefs(payload: ChoiceAnswerList, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    cnt = await upsert_answers(db, user.id, payload.answers, ValuesAnswer, is_text=False)
    return SaveResult(status="success", saved_count=cnt)
@router.get(
    "/essay",
    response_model=GroupInputOut,
    summary="주관식 소개"
)
async def get_group_input(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    q34 = next(q for q in QUESTION_DEFINITIONS if q["id"] == 34)
    stored = await get_group_input_answers(db, user.id)
    return GroupInputOut(
        answers=[
            { **sub, "text": stored.get(sub["id"]) }
            for sub in q34["subQuestions"]
        ]
    )


@router.post(
    "/essay",
    response_model=SaveResult,
    status_code=status.HTTP_201_CREATED,
    summary="주관식 소개 작성"
)
async def post_group_input(payload: GroupInputAnswerList, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    cnt = await upsert_group_input_answers(db, user.id, payload.answers)
    return SaveResult(status="success", saved_count=cnt)