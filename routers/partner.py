from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from deps import get_current_user
from core.database import get_session
from schemas import (
    QuestionOut, QuestionList,
    NewPartnerIn, PartnerOut, PartnerWithAnswersOut
)
from crud import create_partner_with_answers, get_latest_partner

router = APIRouter(prefix="/partners", tags=["partners"])

PARTNER_QUESTIONS = [ {...}, ..., {...} ]

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

@router.get("/latest", response_model=PartnerWithAnswersOut)
async def get_latest(user=Depends(get_current_user), db=Depends(get_session)):
    p = await get_latest_partner(db, user.id)
    if not p:
        raise HTTPException(404,"No partner registered")
    return {
        "id": p.id, "meeting_date": p.meeting_date,
        "answers":[{"question_id":a.question_id,"option_id":a.option_id} for a in p.answers]
    }
