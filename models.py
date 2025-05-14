from sqlalchemy import Column, Integer, String, Boolean, Date, Text, ForeignKey, Time
from sqlalchemy.orm import relationship
from core.database import Base


class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    google_id  = Column(String, unique=True, index=True)
    email      = Column(String, unique=True, index=True)
    name       = Column(String)
    picture    = Column(String, nullable=True)

    profile_initial      = relationship("ProfileInitial",      back_populates="user", uselist=False)
    lifestyle_answers    = relationship("LifestyleAnswer",    cascade="all,delete-orphan")
    trait_answers        = relationship("TraitAnswer",        cascade="all,delete-orphan")
    preference_answers   = relationship("PreferenceAnswer",   cascade="all,delete-orphan")
    values_answers       = relationship("ValuesAnswer",       cascade="all,delete-orphan")
    introduction_answers = relationship("IntroductionAnswer", cascade="all,delete-orphan")
    partners             = relationship("Partner",            cascade="all,delete-orphan")


class ProfileInitial(Base):
    __tablename__ = "profile_initial"
    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name    = Column(String)
    age     = Column(Integer)
    gender  = Column(String)
    job     = Column(String, nullable=True)
    region  = Column(String, nullable=True)
    mbti    = Column(String, nullable=True)
    smoking = Column(Boolean, default=False)

    user = relationship("User", back_populates="profile_initial")


# --- 설문 답변 테이블 ---
class LifestyleAnswer(Base):
    __tablename__ = "lifestyle_answers"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), index=True)
    question_id = Column(Integer, index=True)
    option_id   = Column(String)


class TraitAnswer(Base):
    __tablename__ = "trait_answers"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), index=True)
    question_id = Column(Integer, index=True)
    option_id   = Column(String)


class PreferenceAnswer(Base):
    __tablename__ = "preference_answers"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), index=True)
    question_id = Column(Integer, index=True)
    option_id   = Column(String)


class ValuesAnswer(Base):
    __tablename__ = "values_answers"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), index=True)
    question_id = Column(Integer, index=True)
    option_id   = Column(String)


class IntroductionAnswer(Base):
    __tablename__ = "introduction_answers"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), index=True)
    question_id = Column(Integer, index=True)
    text        = Column(Text)

class GroupInputAnswer(Base):
    __tablename__ = "group_input_answers"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), index=True)
    question_id     = Column(Integer, index=True, default=34)        
    sub_question_id = Column(Integer, index=True)                    
    text            = Column(Text, nullable=True)

class Partner(Base):
    __tablename__ = "partners"
    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, ForeignKey("users.id"), index=True)

    answers  = relationship(
        "PartnerAnswer",
        back_populates="partner",
        cascade="all,delete-orphan",
        lazy="selectin",
    )

class Schedule(Base):
    __tablename__ = "schedules"
    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), index=True)
    meeting_date   = Column(Date, nullable=False)
    meeting_time   = Column(Time, nullable=False)
    meeting_place  = Column(String, nullable=False)

class PartnerAnswer(Base):
    __tablename__ = "partner_answers"
    id          = Column(Integer, primary_key=True, index=True)
    partner_id  = Column(Integer, ForeignKey("partners.id"), index=True)
    question_id = Column(Integer, index=True)
    option_id   = Column(String)

    partner = relationship("Partner", back_populates="answers")

class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id    = Column(Integer, primary_key=True, index=True)
    text  = Column(String, nullable=False)           

    model_config = {"from_attributes": True}

class UserChecklist(Base):
    __tablename__ = "user_checklists"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), index=True)
    item_id    = Column(Integer, ForeignKey("checklist_items.id"), index=True)
    date       = Column(Date, index=True)  
    checked    = Column(Boolean, default=True) 

    item = relationship("ChecklistItem")