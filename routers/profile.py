from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from deps import get_current_user
from core.database import get_session
from crud import get_profile, upsert_basic, upsert_extra
from schemas import ProfileIn, UserProfileOut

router = APIRouter(prefix="/users/me", tags=["profile"])

@router.get(
    "/profile",
    response_model=UserProfileOut,
    summary="내 프로필 조회",
)
async def read_profile(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    profile = await get_profile(db, user.id)
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "profile": profile,
    }
    
@router.post(
    "/profile",
    response_model=UserProfileOut,
    status_code=status.HTTP_201_CREATED,
    summary="내 프로필 저장/업데이트"
)
async def upsert_profile(
    data: ProfileIn,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await upsert_basic(db, user.id, data)

    await upsert_extra(db, user.id, data)

    profile = await get_profile(db, user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 저장 후 조회에 실패했습니다."
        )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "profile": profile,
    }
