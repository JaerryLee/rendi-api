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
    """
    - 이름/나이/성별 등 기본 정보 + 직업/거주지역/MBTI/흡연여부를 한 번에 저장합니다.
    - region, mbti는 선택, smoking은 필수입니다.
    - 성공 시 전체 유저+프로필을 반환합니다.
    """
    # 1) 기본 정보 저장 (생성 또는 업데이트)
    await upsert_basic(db, user.id, data)

    # 2) 추가 정보 저장
    await upsert_extra(db, user.id, data)

    # 3) 최종 프로필 조회
    profile = await get_profile(db, user.id)
    if profile is None:
        # upsert_basic/extra가 정상이라면 이 케이스는 거의 발생하지 않습니다.
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
