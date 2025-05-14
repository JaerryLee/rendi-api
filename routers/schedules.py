from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from deps import get_current_user
from core.database import get_session
from schemas import ScheduleIn, ScheduleOut
from crud import upsert_schedule, get_schedule_by_user
from typing import List, Optional

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.post(
    "",
    response_model=ScheduleOut,
    summary="일정 등록/수정"
)
async def set_schedule(
    payload: ScheduleIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    sched = await upsert_schedule(
        db,
        user.id,
        payload.meeting_date,
        payload.meeting_time,
        payload.meeting_place
    )
    return sched

@router.get(
    "",
    response_model=Optional[ScheduleOut],
    summary="내 일정 조회"
)
async def get_schedule(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    sched = await get_schedule_by_user(db, user.id)
    if not sched:
        from datetime import date, time
        sched = await upsert_schedule(
            db,
            user.id,
            meeting_date=date.today(),
            meeting_time=time(hour=0, minute=0),
            meeting_place=""  # 빈 문자열로 초기화
        )
    return sched