#schemas.py
from pydantic import BaseModel, RootModel, Field
from typing import List, Optional, Literal
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


class SubQuestionDef(BaseModel):
    """group_input(subQuestions) 정의"""
    id: int
    title: str
    placeholder: Optional[str] = None
    required: bool = False


class QuestionOut(BaseModel):
    id: int
    type: str               # 'select' | 'slider' | 'multiple_choice' | 'group_input'
    title: str

    # select / multiple_choice
    maxChoice: Optional[int] = None
    options: Optional[List[OptionOut]] = None

    # slider
    minLabel: Optional[str] = None
    maxLabel: Optional[str] = None
    min: Optional[int]      = None
    max: Optional[int]      = None
    step: Optional[int]     = None

    # group_input
    subQuestions: Optional[List[SubQuestionDef]] = None

    model_config = {"populate_by_name": True}


class QuestionList(RootModel[List[QuestionOut]]):
    pass


class ChoiceAnswerIn(BaseModel):
    question_id: int = Field(..., description="QUESTION_DEFINITIONS 상의 id")
    option_id: Optional[str]   = Field(None, description="단일 선택 시")
    option_ids: Optional[List[str]] = Field(None, description="복수 선택 시")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": 21,
                "option_ids": ["1", "3", "5"]
            }
        }


class ChoiceAnswerList(BaseModel):
    answers: List[ChoiceAnswerIn]


class SaveResult(BaseModel):
    status: str       = Field(..., example="success")
    saved_count: int  = Field(..., example=3)

class QuestionWithAnswerOut(QuestionOut):
    answer_ids: Optional[List[str]] = None
    text: Optional[str]            = None

    model_config = {"from_attributes": True}
    
class SubQuestionAnswerIn(BaseModel):
    sub_question_id: int = Field(..., ge=1, le=4, description="34번 질문 내 서브 id")
    text: Optional[str]  = Field(None, description="입력 텍스트")

    class Config:
        json_schema_extra = {
            "example": {"sub_question_id": 2, "text": "내 장점은 …"}
        }


class GroupInputAnswerList(BaseModel):
    answers: List[SubQuestionAnswerIn]


class SubQuestionOut(SubQuestionDef):
    text: Optional[str] = None


class GroupInputOut(BaseModel):
    question_id: Literal[34] = 34
    answers: List[SubQuestionOut]
    
# --- 파트너 ---    
class NewPartnerIn(BaseModel):
    answers: List[ChoiceAnswerIn]

class PartnerOut(BaseModel):
    id: int
    model_config = {"from_attributes": True}

class PartnerAnswerOut(BaseModel):
    question_id: int
    option_id: str

class PartnerWithAnswersOut(PartnerOut):
    answers: List[PartnerAnswerOut]

class PartnerListOut(BaseModel):
    partners: List[PartnerWithAnswersOut]

class ScheduleIn(BaseModel):
    meeting_date: Optional[date] = Field(None, example="2025-05-14")
    meeting_time: Optional[time] = Field(None, example="09:24")
    meeting_place: Optional[str] = Field(None, example="카페 ABC")

    model_config = {
        "json_schema_extra": {
            "example": {
                "meeting_date": "2025-05-14",
                "meeting_time": "09:24",
                "meeting_place": "카페 ABC"
            }
        }
    }
    
class ScheduleOut(BaseModel):
    meeting_date: Optional[date] = Field(
        None,
        example="2025-05-14"
    )
    meeting_time: Optional[time] = Field(
        None,
        example="09:24"
    )
    meeting_place: Optional[str] = Field(
        None,
        example="카페 ABC"
    )

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            time: lambda t: t.strftime("%H:%M")
        },
    }

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

# 체크리스트

class UserChecklistStatus(BaseModel):
    item_id: int
    checked: bool

class ToggleChecklistIn(BaseModel):
    item_id: int
    checked: bool

class ChecklistItemOut(BaseModel):
    id: int
    text: str

    model_config = {"from_attributes": True}