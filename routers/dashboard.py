from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from deps import get_current_user
from crud import get_latest_partner
from schemas import DashboardOut, TaskOut, ActionOut
from core.database import get_session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("", response_model=DashboardOut)
async def get_dashboard(user=Depends(get_current_user), db: AsyncSession=Depends(get_session)):
    p = await get_latest_partner(db, user.id)
    if not p:
        return DashboardOut(partner=None, countdown="", tasks=[], actions=[])
    delta = (p.meeting_date - date.today()).days
    cd = f"D-{delta}" if delta>0 else ("D-Day" if delta==0 else f"D+{abs(delta)}")
    tasks = [
        TaskOut(id="d-1", when="D-1", title="하루 전"),
        TaskOut(id="d-day", when="D-Day", title="소개팅 당일"),
        TaskOut(id="d+1", when="D+1", title="다음 날"),
    ]
    actions = [
        ActionOut(id="coaching",   title="소개팅 실시간 코칭"),
        ActionOut(id="retrospect", title="소개팅 회고"),
    ]
    # 
    return DashboardOut(partner=p, countdown=cd, tasks=tasks, actions=actions)
