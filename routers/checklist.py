from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from constants import CHECKLIST_ITEMS
from deps import get_current_user
from core.database import get_session
from crud import get_all_items, get_user_checklist, upsert_user_check
from schemas import UserChecklistStatus, ToggleChecklistIn, ChecklistItemOut

router = APIRouter(prefix="/checklist", tags=["checklist"])

@router.get(
    "/items",
    response_model=List[ChecklistItemOut],
    summary="체크리스트 기본 항목 리스트 조회"
)
async def list_default_items():
    """
    체크리스트에 사용할 기본 항목 텍스트 목록을 반환합니다.
    """
    return CHECKLIST_ITEMS

@router.get(
    "",
    response_model=List[UserChecklistStatus],
    summary="체크리스트 상태 조회"
)
async def get_checklist(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    현재 사용자가 체크한 항목의 상태를 반환합니다.
    """
    items = await get_all_items(db)
    user_recs = {rec.item_id: rec.checked for rec in await get_user_checklist(db, user.id)}

    return [
        UserChecklistStatus(item_id=item.id, checked=user_recs.get(item.id, False))
        for item in items
    ]

@router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="체크/해제 토글"
)
async def toggle_check(
    payload: ToggleChecklistIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    특정 항목(item_id)에 대해 체크 또는 해제 상태를 업데이트합니다.
    """
    await upsert_user_check(db, user.id, payload.item_id, payload.checked)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
