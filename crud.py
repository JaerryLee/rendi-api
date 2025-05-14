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
    ChecklistItem, UserChecklist,
    GroupInputAnswer, Schedule
)
from schemas import ChoiceAnswerIn, ProfileIn, SubQuestionAnswerIn
from typing import Dict, List
from sqlalchemy.orm import selectinload

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
    data: ProfileIn            
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
    data: ProfileIn            
) -> ProfileInitial:
    p = await get_profile(db, user_id)
    p.job     = data.job
    p.region  = data.region
    p.mbti    = data.mbti
    p.smoking = data.smoking
    await db.commit()
    await db.refresh(p)
    return p

# --- 설문 공통 ---
async def upsert_answers(
    db: AsyncSession,
    user_id: int,
    answers: List,
    model_cls,
    is_text: bool = False
) -> int:
    await db.execute(delete(model_cls).where(model_cls.user_id == user_id))
    objs = []
    if is_text:
        for a in answers:
            objs.append(model_cls(
                user_id=user_id,
                question_id=a.question_id,
                text=a.text
            ))
    else:
        for a in answers:
            for oid in a.option_ids:
                objs.append(model_cls(
                    user_id=user_id,
                    question_id=a.question_id,
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
    r = await db.execute(select(model).where(model.user_id == user_id))
    rows = r.scalars().all()
    d: Dict[int, List[str]] = {}
    for row in rows:
        key = row.question_id
        val = getattr(row, "option_id", None) or getattr(row, "text", None)
        d.setdefault(key, []).append(val)
    return d


async def get_group_input_answers(
    db: AsyncSession, user_id: int
) -> Dict[int, str]:
    r = await db.execute(
        select(GroupInputAnswer).filter_by(user_id=user_id, question_id=34)
    )
    rows = r.scalars().all()
    return {row.sub_question_id: row.text for row in rows}


async def upsert_group_input_answers(
    db: AsyncSession,
    user_id: int,
    answers: List[SubQuestionAnswerIn]
) -> int:
    await db.execute(
        delete(GroupInputAnswer).filter_by(user_id=user_id, question_id=34)
    )
    objs = [
        GroupInputAnswer(
            user_id=user_id,
            question_id=34,
            sub_question_id=a.sub_question_id,
            text=a.text
        )
        for a in answers
    ]
    db.add_all(objs)
    await db.commit()
    return len(objs)

# --- 파트너 ---
async def create_partner_with_answers(
    db: AsyncSession,
    user_id: int,
    answers: List[ChoiceAnswerIn]
) -> Partner:
    partner = Partner(user_id=user_id)
    db.add(partner)
    await db.flush()

    objs = []
    for ans in answers:
        ids = ans.option_ids or ([ans.option_id] if ans.option_id else [])
        for oid in ids:
            objs.append(PartnerAnswer(
                partner_id=partner.id,
                question_id=ans.question_id,
                option_id=oid
            ))
    db.add_all(objs)
    await db.commit()
    await db.refresh(partner)
    return partner

async def upsert_partner_answers(
    db: AsyncSession,
    user_id: int,
    answers: List[ChoiceAnswerIn]
) -> Partner:
    r = await db.execute(
        select(Partner)
        .where(Partner.user_id == user_id)
        .order_by(Partner.id.desc())
        .limit(1)
    )
    partner = r.scalars().first()
    if not partner:
        # 없으면 신규 생성
        return await create_partner_with_answers(db, user_id, answers)

    # 기존 답변 삭제 후 새로 삽입
    await db.execute(
        delete(PartnerAnswer)
        .where(PartnerAnswer.partner_id == partner.id)
    )
    objs = []
    for ans in answers:
        ids = ans.option_ids or ([ans.option_id] if ans.option_id else [])
        for oid in ids:
            objs.append(PartnerAnswer(
                partner_id=partner.id,
                question_id=ans.question_id,
                option_id=oid
            ))
    db.add_all(objs)
    await db.commit()
    await db.refresh(partner)
    return partner

async def get_all_partners(
    db: AsyncSession,
    user_id: int
) -> List[Partner]:
    r = await db.execute(
        select(Partner)
        .where(Partner.user_id == user_id)
        .options(selectinload(Partner.answers))
        .order_by(Partner.id.desc())
    )
    return r.scalars().all()

async def get_latest_partner(
    db: AsyncSession,
    user_id: int
) -> Partner | None:
    r = await db.execute(
        select(Partner)
        .where(Partner.user_id == user_id)
        .options(selectinload(Partner.answers))
        .order_by(Partner.id.desc())
        .limit(1)
    )
    return r.scalars().first()

async def upsert_schedule(
    db: AsyncSession,
    user_id: int,
    meeting_date: date,
    meeting_time: time,
    meeting_place: str
) -> Schedule:
    # 이미 user_id로 저장된 스케줄 조회
    r = await db.execute(
        select(Schedule).where(Schedule.user_id == user_id)
    )
    sched = r.scalars().first()

    if sched:
        # 있으면 수정
        sched.meeting_date  = meeting_date
        sched.meeting_time  = meeting_time
        sched.meeting_place = meeting_place
    else:
        # 없으면 신규 생성
        sched = Schedule(
            user_id=user_id,
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            meeting_place=meeting_place
        )
        db.add(sched)

    await db.commit()
    await db.refresh(sched)
    return sched

async def get_schedule_by_user(
    db: AsyncSession,
    user_id: int
) -> Schedule | None:
    r = await db.execute(
        select(Schedule).where(Schedule.user_id == user_id)
    )
    return r.scalars().first()

async def get_all_items(db: AsyncSession) -> List[ChecklistItem]:
    r = await db.execute(select(ChecklistItem))
    return r.scalars().all()

async def get_user_checklist(db: AsyncSession, user_id: int) -> list[UserChecklist]:
    r = await db.execute(
        select(UserChecklist).where(UserChecklist.user_id == user_id)
    )
    return r.scalars().all()

async def upsert_user_check(
    db: AsyncSession, user_id: int, item_id: int, checked: bool
) -> None:
    r = await db.execute(
        select(UserChecklist).where(
            UserChecklist.user_id == user_id,
            UserChecklist.item_id == item_id
        )
    )
    rec = r.scalars().first()
    if rec:
        rec.checked = checked
    else:
        rec = UserChecklist(user_id=user_id, item_id=item_id, checked=checked)
        db.add(rec)
    await db.commit()