from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List, Optional

from deps import get_current_user
from core.database import get_session
from crud import (
    get_all_items,
    get_user_checklist,
    upsert_user_check
)
from schemas import (
    ChecklistItemOut,
    DailyChecklistOut,
    ToggleChecklistIn,
    UserChecklistStatus
)

router = APIRouter(prefix="/checklist", tags=["checklist"])

@router.get(
    "/items",
    response_model=List[ChecklistItemOut],
    summary="체크리스트 항목 전체 조회"
)
async def list_items(db: AsyncSession = Depends(get_session)):
    return await get_all_items(db)


@router.get(
    "",
    response_model=DailyChecklistOut,
    summary="특정 날짜(기본: 오늘)의 체크리스트 상태 조회"
)
async def get_today_checklist(
    for_date: date = Query(default=None),
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if for_date is None:
        for_date = date.today()
    items = await get_all_items(db)
    user_recs = {r.item_id: r.checked for r in await get_user_checklist(db, user.id, for_date)}

    statuses = [
        UserChecklistStatus(item_id=item.id, checked=user_recs.get(item.id, False))
        for item in items
    ]
    return DailyChecklistOut(date=for_date, items=statuses)


@router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="체크/해제 토글"
)
async def toggle_check(
    payload: ToggleChecklistIn,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    await upsert_user_check(db, user.id, date.today(), payload.item_id, payload.checked)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
