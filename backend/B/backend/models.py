from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

# --- 1. 유저 정보 테이블 ---
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    
    # [요구사항 2] 가입일(signup_date)로 활용할 필드: timezone=True 설정 확인 완료
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
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
    
    # [요구사항 1] 신규 필드 추가
    # routine_category: 활동형, 휴식형 등 루틴 유형 저장
    routine_category = Column(String, nullable=True)
    # score_diff: 루틴 수행 전후의 마음 온도 변화량 (난이도 결정 지표)
    score_diff = Column(Float, default=0.0)

    is_done = Column(Boolean, default=False)

    emotion = Column(String, nullable=True)

    # 8가지 감정 수치
    joy = Column(Float, default=0.0)
    sadness = Column(Float, default=0.0)
    anger = Column(Float, default=0.0)
    fear = Column(Float, default=0.0)
    trust = Column(Float, default=0.0)
    disgust = Column(Float, default=0.0)
    surprise = Column(Float, default=0.0)
    anticipation = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    analysis_comment = Column(String)
    
    author = relationship("User", back_populates="diaries")
    analysis_data = relationship("Analysis", back_populates="diary", uselist=False)


# --- 3. 개별 일기 심층 분석 테이블 ---
class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    diary_id = Column(Integer, ForeignKey("diaries.id"))
    emotion = Column(String) 
    score = Column(Float, default=0.0) 
    feedback = Column(Text)

    diary = relationship("Diary", back_populates="analysis_data")


# --- 4~7. 설문 및 챗봇 테이블 (기존 동일) ---
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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="survey_results")

class ChatHistory(Base):
    __tablename__ = "chat_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="chat_histories")