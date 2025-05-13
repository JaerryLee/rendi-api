from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from datetime import date, time
from models import (
    User, ProfileInitial,
    LifestyleAnswer, TraitAnswer,
    PreferenceAnswer, ValuesAnswer,
    IntroductionAnswer,
    Partner, PartnerAnswer,
    ChecklistItem, UserChecklist
)
from schemas import ChoiceAnswerIn, TextAnswerIn, ProfileIn  # ProfileBasicIn/ExtraIn → ProfileIn
from typing import Dict, List

# --- 유저 ---
async def get_user_by_google_id(db: AsyncSession, google_id: str):
    r = await db.execute(select(User).where(User.google_id == google_id))
    return r.scalars().first()

async def create_user(db: AsyncSession, google_id, email, name, picture):
    user = User(google_id=google_id, email=email, name=name, picture=picture)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# --- 프로필 ---
async def get_profile(db: AsyncSession, user_id: int) -> ProfileInitial | None:
    r = await db.execute(
        select(ProfileInitial).where(ProfileInitial.user_id == user_id)
    )
    return r.scalars().first()

async def upsert_basic(
    db: AsyncSession,
    user_id: int,
    data: ProfileIn            # ProfileBasicIn → ProfileIn
) -> ProfileInitial:
    p = await get_profile(db, user_id)
    if p:
        p.name   = data.name
        p.age    = data.age
        p.gender = data.gender
    else:
        p = ProfileInitial(
            user_id=user_id,
            name=data.name,
            age=data.age,
            gender=data.gender
        )
        db.add(p)
    await db.commit()
    await db.refresh(p)
    return p

async def upsert_extra(
    db: AsyncSession,
    user_id: int,
    data: ProfileIn            # ProfileExtraIn → ProfileIn
) -> ProfileInitial:
    p = await get_profile(db, user_id)
    # 기본 정보가 반드시 있어야 함
    p.job     = data.job
    p.region  = data.region
    p.mbti    = data.mbti
    p.smoking = data.smoking
    await db.commit()
    await db.refresh(p)
    return p

# --- 설문 공통 ---
async def upsert_answers(
    db: AsyncSession, user_id: int,
    answers, model_cls, is_text: bool = False
):
    await db.execute(delete(model_cls).where(model_cls.user_id == user_id))
    objs = []
    if is_text:
        for ans in answers:
            objs.append(model_cls(
                user_id=user_id,
                question_id=ans.question_id,
                text=ans.text
            ))
    else:
        for ans in answers:
            if ans.option_id:
                objs.append(model_cls(
                    user_id=user_id,
                    question_id=ans.question_id,
                    option_id=ans.option_id
                ))
            if ans.option_ids:
                for oid in ans.option_ids:
                    objs.append(model_cls(
                        user_id=user_id,
                        question_id=ans.question_id,
                        option_id=oid
                    ))
    db.add_all(objs)
    await db.commit()
    return len(objs)

async def get_user_answers(
    db: AsyncSession,
    user_id: int,
    model
) -> Dict[int, List[str]]:
    """
    model 테이블에서 user_id 에 대한 question별 option_id(text) 리스트를 반환.
    """
    r = await db.execute(
        select(model).where(model.user_id==user_id)
    )
    rows = r.scalars().all()
    d: Dict[int, List[str]] = {}
    for row in rows:
        key = row.question_id
        val = getattr(row, "option_id", None) or getattr(row, "text", None)
        d.setdefault(key, []).append(val)
    return d

# --- 파트너 ---
async def create_partner_with_answers(
    db: AsyncSession,
    user_id: int,
    meeting_date: date,
    answers: list[ChoiceAnswerIn]
) -> Partner:
    partner = Partner(user_id=user_id, meeting_date=meeting_date)
    db.add(partner)
    await db.flush()

    answer_objs = [
        PartnerAnswer(partner_id=partner.id, question_id=ans.question_id, option_id=ans.option_id)
        for ans in answers
    ]
    db.add_all(answer_objs)
    await db.commit()
    await db.refresh(partner)
    return partner

async def get_latest_partner(db: AsyncSession, user_id: int) -> Partner | None:
    r = await db.execute(
        select(Partner)
        .where(Partner.user_id == user_id)
        .order_by(Partner.id.desc())
        .limit(1)
    )
    return r.scalars().first()

async def get_all_partners(db: AsyncSession, user_id: int) -> List[Partner]:
    r = await db.execute(
        select(Partner)
        .where(Partner.user_id == user_id)
        .order_by(Partner.id.desc())
    )
    return r.scalars().all()

async def update_latest_partner_schedule(
    db: AsyncSession,
    user_id: int,
    meeting_date: date,
    meeting_time: time,
    meeting_place: str
) -> Partner:
    # 1) 가장 최신 파트너 가져오기
    r = await db.execute(
        select(Partner)
        .where(Partner.user_id == user_id)
        .order_by(Partner.id.desc())
        .limit(1)
    )
    partner = r.scalars().first()
    if not partner:
        raise ValueError("No partner found to schedule")

    # 2) 스케줄 데이터 업데이트
    partner.meeting_date  = meeting_date
    partner.meeting_time  = meeting_time
    partner.meeting_place = meeting_place

    # 3) 커밋 & 리프레시
    await db.commit()
    await db.refresh(partner)
    return partner

async def get_all_items(db: AsyncSession) -> List[ChecklistItem]:
    r = await db.execute(select(ChecklistItem))
    return r.scalars().all()

async def get_user_checklist(
    db: AsyncSession, user_id: int, for_date: date
) -> List[UserChecklist]:
    r = await db.execute(
        select(UserChecklist)
        .where(UserChecklist.user_id == user_id)
        .where(UserChecklist.date == for_date)
    )
    return r.scalars().all()

async def upsert_user_check(
    db: AsyncSession, user_id: int, for_date: date, item_id: int, checked: bool
) -> None:
    # 이미 존재하면 업데이트, 없으면 삽입
    r = await db.execute(
        select(UserChecklist)
        .where(UserChecklist.user_id == user_id)
        .where(UserChecklist.date == for_date)
        .where(UserChecklist.item_id == item_id)
    )
    rec = r.scalars().first()
    if rec:
        rec.checked = checked
    else:
        rec = UserChecklist(
            user_id=user_id,
            date=for_date,
            item_id=item_id,
            checked=checked
        )
        db.add(rec)
    await db.commit()