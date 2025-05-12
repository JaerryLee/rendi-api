from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from deps import get_current_user
from core.database import get_session
from crud import get_profile, upsert_basic, upsert_extra
from schemas import ProfileBasicIn, ProfileExtraIn, UserProfileOut
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
    """
    - 로그인된 유저의 프로필을 조회합니다.
    - 프로필이 없으면 `profile` 필드는 null 로 내려갑니다.
    """
    profile = await get_profile(db, user.id)
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "profile": profile,
    }


@router.post(
    "/profile/basic",
    response_model=UserProfileOut,
    status_code=status.HTTP_201_CREATED,
    summary="기본 정보 저장",
)
async def write_basic_profile(
    data: ProfileBasicIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    - 이름/나이/성별 등 기본 정보를 저장합니다.
    - 성공 시 전체 유저+프로필을 반환합니다.
    """
    prof = await upsert_basic(db, user.id, data)
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "profile": prof,
    }


@router.post(
    "/profile/extra",
    response_model=UserProfileOut,
    summary="추가 정보 저장",
)
async def write_extra_profile(
    data: ProfileExtraIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    - 직업/거주지역/MBTI/흡연여부 등 추가 정보를 저장합니다.
    - 기본 정보가 아직 없다면 400 에러를 반환합니다.
    """
    existing = await get_profile(db, user.id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="먼저 기본 정보를 저장해주세요."
        )

    prof = await upsert_extra(db, user.id, data)
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "profile": prof,
    }