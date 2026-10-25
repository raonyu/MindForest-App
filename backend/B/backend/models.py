import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float, Date
from database import Base
from sqlalchemy.orm import relationship

# --- 1. 유저 정보 테이블 ---
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)

    # [요구사항 2] 가입일(signup_date) 필드: Python 3.14 호환을 위해 datetime.datetime.now 사용
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    is_onboarding_done = Column(Boolean, default=False)
    user_animal = Column(String, nullable=True)
    assigned_category = Column(String, nullable=True)

    diaries = relationship("Diary", back_populates="author")
    survey_results = relationship("SurveyResult", back_populates="user")
    chat_histories = relationship("ChatHistory", back_populates="user")
    survey_answers = relationship("SurveyAnswer", back_populates="user")


# --- 2. 일기 및 감정 데이터 테이블 ---
class Diary(Base):
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    content = Column(Text)

    # 루틴 데이터
    routine_name = Column(String, nullable=True)
    routine_category = Column(String, nullable=True)
    score_diff = Column(Float, nullable=True)
    is_done = Column(Boolean, default=False)

    # 사용자 Self-Report - 첫 번째 감정
    emotion = Column(String, nullable=True)
    emotion_intensity = Column(Integer, nullable=True)

    # 사용자 Self-Report - 두 번째 감정
    secondary_emotion = Column(String, nullable=True)
    secondary_emotion_intensity = Column(Integer, nullable=True)

    # AI 8가지 감정 수치
    joy = Column(Float, default=0.0)
    sadness = Column(Float, default=0.0)
    anger = Column(Float, default=0.0)
    fear = Column(Float, default=0.0)
    trust = Column(Float, default=0.0)
    disgust = Column(Float, default=0.0)
    surprise = Column(Float, default=0.0)
    anticipation = Column(Float, default=0.0)

    keywords = Column(String, nullable=True)
    analysis_status = Column(String, default="idle", nullable=False)
    confidence = Column(Float, nullable=True)
    bws_used = Column(Boolean, default=False, nullable=False)
    analysis_completed_at = Column(DateTime(timezone=True), nullable=True)
    analysis_error = Column(String, nullable=True)
    analysis_requested_at = Column(DateTime(timezone=True), nullable=True)


    # 일기 수정 후 이전 분석 결과가 덮어쓰는 것 방지
    analysis_version = Column(Integer, default=0, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    analysis_comment = Column(String, nullable=True)

    author = relationship("User", back_populates="diaries")
    analysis_data = relationship(
        "Analysis",
        back_populates="diary",
        uselist=False
    )

# --- 3. 개별 일기 심층 분석 테이블 ---
class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    diary_id = Column(Integer, ForeignKey("diaries.id"))
    emotion = Column(String)
    score = Column(Float, default=0.0)
    feedback = Column(Text)

    diary = relationship("Diary", back_populates="analysis_data")


# --- 3-1. 복합 감정(BWS) 판별 기록 테이블 ---
class BwsRecord(Base):
    """감정 점수가 비슷하게 경합해서 BWS 검증을 돌린 날의 기록."""
    __tablename__ = "bws_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    diary_id = Column(Integer, ForeignKey("diaries.id"))

    # 경합한 후보 감정 (쉼표 구분, 예: "sadness,anger")
    candidates = Column(String)
    best_emotion = Column(String, nullable=True)
    worst_emotion = Column(String, nullable=True)
    reasoning = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))


# --- 4. 설문 관련 테이블 ---
class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True, index=True)
    survey_type = Column(String)
    question_num = Column(Integer)
    question_text = Column(Text)

class SurveyAnswer(Base):
    __tablename__ = "survey_answers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    survey_type = Column(String)
    question_num = Column(Integer)
    answer = Column(Integer)
    user = relationship("User", back_populates="survey_answers")

class SurveyResult(Base):
    __tablename__ = "survey_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    survey_type = Column(String)
    score = Column(Integer)
    result_message = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    user = relationship("User", back_populates="survey_results")


# --- 5. 챗봇 및 기타 테이블 ---
class ChatHistory(Base):
    __tablename__ = "chat_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    user = relationship("User", back_populates="chat_histories")

class Animal(Base):
    __tablename__ = "animals"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), unique=True, index=True)
    name = Column(String(50))
    emoji = Column(String(10))
    description = Column(Text)

class RoutineMaster(Base):
    __tablename__ = "routine_master"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)
    level = Column(Integer)
    content = Column(Text)

class UserRoutine(Base):
    __tablename__ = "user_routines"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    routine_id = Column(Integer, ForeignKey("routine_master.id"))

    # [오류 해결] datetime 모듈의 date.today를 사용하여 할당된 날짜를 정확히 기록
    date = Column(Date, default=datetime.date.today)

    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    routine_detail = relationship("RoutineMaster")


class RoutineObservation(Base):
    __tablename__ = "routine_observations"
    id = Column(Integer, primary_key=True)
    user_routine_id = Column(Integer, ForeignKey("user_routines.id"), unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    before_diary_id = Column(Integer, nullable=True)
    before_version = Column(Integer, nullable=True)
    before_temperature = Column(Float, nullable=True)
    after_diary_id = Column(Integer, nullable=True)
    after_version = Column(Integer, nullable=True)
    after_temperature = Column(Float, nullable=True)
    measured_at = Column(DateTime(timezone=True), nullable=True)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    diary_id = Column(Integer, index=True)
    analysis_version = Column(Integer)
    status = Column(String, nullable=False)
    total_ms = Column(Float, nullable=False)
    model_ms = Column(Float, nullable=True)
    bws_ms = Column(Float, nullable=True)
    bws_attempted = Column(Boolean, default=False)
    bws_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
