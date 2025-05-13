#schemas.py
from pydantic import BaseModel, RootModel, Field
from typing import List, Optional
from datetime import date, time

# --- 유저 공통 스키마 ---
class UserOut(BaseModel):
    id: int
    email: str
    name: str
    picture: Optional[str]

    model_config = {"from_attributes": True}


# --- 토큰 스키마 ---
class TokenOut(BaseModel):
    access_token: str
    refresh_token: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "dGhpc19pc19hX3JlZnJlc2hfdG9rZW4..."
            }
        }
    }


# --- 프로필 온보딩용 입력 스키마 ---
class ProfileIn(BaseModel):
    # --- 기본 정보 ---
    name: str
    age: int
    gender: str

    # --- 추가 정보 ---
    job: Optional[str]            = Field(None, description="직업")
    region: Optional[str]         = Field(None, description="거주 지역 (선택)")
    mbti: Optional[str]           = Field(None, description="MBTI (선택)")
    smoking: bool                 = Field(..., description="흡연 여부 (필수)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "홍길동",
                "age": 28,
                "gender": "male",
                "job": "Developer",
                "region": "Seoul",
                "mbti": "INTJ",
                "smoking": True
            }
        }
    }


# --- DB 모델 리턴용 프로필 아웃풋 ---
class ProfileInitialOut(BaseModel):
    name: str
    age: int
    gender: str
    job: Optional[str]
    region: Optional[str]
    mbti: Optional[str]
    smoking: bool

    model_config = {"from_attributes": True}


# --- 유저+프로필 전체 반환 ---
class UserProfileOut(UserOut):
    profile: Optional[ProfileInitialOut]


# --- 설문 ---
class OptionOut(BaseModel):
    label: str
    value: str

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: int
    type: str               # 'select' | 'slider' | 'multiple_choice' | 'group_input'
    title: str
    maxChoice: Optional[int]
    options: Optional[List[OptionOut]]
    subQuestions: Optional[List[OptionOut]]  # group_input 용
    minLabel: Optional[str]  # slider 용
    maxLabel: Optional[str]
    min: Optional[int]
    max: Optional[int]
    step: Optional[int]

    model_config = {"populate_by_name": True}


class QuestionList(RootModel[List[QuestionOut]]):
    pass


class ChoiceAnswerIn(BaseModel):
    question_id: int
    option_id: Optional[str]
    option_ids: Optional[List[str]]


class ChoiceAnswerList(BaseModel):
    answers: List[ChoiceAnswerIn]


class TextAnswerIn(BaseModel):
    question_id: int
    text: str


class SaveResult(BaseModel):
    status: str
    saved_count: int

class QuestionWithAnswerOut(BaseModel):
    id: int
    type: str
    title: str
    maxChoice: Optional[int]
    options: Optional[List[OptionOut]]
    subQuestions: Optional[List[OptionOut]]
    minLabel: Optional[str]
    maxLabel: Optional[str]
    min: Optional[int]
    max: Optional[int]
    step: Optional[int]

    answer_id: Optional[str] = None
    answer_ids: Optional[List[str]] = None
    text: Optional[str]       = None           

    model_config = {
        "from_attributes": True
    }
    
# --- 파트너 ---
class NewPartnerIn(BaseModel):
    meeting_date: date
    answers: List[ChoiceAnswerIn]
    
class ScheduleIn(BaseModel):
    meeting_date: date
    meeting_time: time
    meeting_place: str

class PartnerAnswerOut(BaseModel):
    question_id: int
    option_id: str

class PartnerOut(BaseModel):
    id: int
    meeting_date: date
    meeting_time: Optional[time]
    meeting_place: Optional[str]

    model_config = {"from_attributes": True}

class PartnerWithAnswersOut(PartnerOut):
    answers: List[PartnerAnswerOut]

class PartnerListOut(BaseModel):
    partners: List[PartnerWithAnswersOut]

# --- 대시보드 ---
class TaskOut(BaseModel):
    id: str
    when: str
    title: str


class ActionOut(BaseModel):
    id: str
    title: str


class DashboardOut(BaseModel):
    partner: PartnerOut
    countdown: str
    tasks: List[TaskOut]
    actions: List[ActionOut]

# 체크리스튼튼

class ChecklistItemOut(BaseModel):
    id: int
    text: str
    class Config:
        from_attributes = True

class UserChecklistStatus(BaseModel):
    item_id: int
    checked: bool

class DailyChecklistOut(BaseModel):
    date: date
    items: List[UserChecklistStatus]

class ToggleChecklistIn(BaseModel):
    item_id: int
    checked: bool