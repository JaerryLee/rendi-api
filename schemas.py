from pydantic import BaseModel, RootModel
from typing import List, Optional
from datetime import date

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
class ProfileBasicIn(BaseModel):
    name: str
    age: int
    gender: str

class ProfileExtraIn(BaseModel):
    job: Optional[str]
    region: Optional[str]
    mbti: Optional[str]
    smoking: Optional[bool] = False


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


# --- 설문 공통 ---
class OptionOut(BaseModel):
    id: str
    text: str

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: int
    text: str
    multiple: bool
    options: List[OptionOut]

    model_config = {"from_attributes": True}


class QuestionList(RootModel[List[QuestionOut]]):
    """
    선택형 문항 리스트 반환용 루트 모델
    """
    pass


class ChoiceAnswerIn(BaseModel):
    question_id: int
    option_id: Optional[str]
    option_ids: Optional[List[str]]


class ChoiceAnswerList(BaseModel):
    answers: List[ChoiceAnswerIn]


class TextQuestionOut(BaseModel):
    id: int
    prompt: str

    model_config = {"from_attributes": True}


class TextQuestionList(RootModel[List[TextQuestionOut]]):
    """
    주관식 문항 리스트 반환용 루트 모델
    """
    pass


class TextAnswerIn(BaseModel):
    question_id: int
    text: str


class TextAnswerList(BaseModel):
    answers: List[TextAnswerIn]


class SaveResult(BaseModel):
    status: str
    saved_count: int


# --- 파트너 ---
class NewPartnerIn(BaseModel):
    meeting_date: date
    answers: List[ChoiceAnswerIn]


class PartnerOut(BaseModel):
    id: int
    meeting_date: date

    model_config = {"from_attributes": True}


class PartnerAnswerOut(BaseModel):
    question_id: int
    option_id: str


class PartnerWithAnswersOut(PartnerOut):
    answers: List[PartnerAnswerOut]


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
