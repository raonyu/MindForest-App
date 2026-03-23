from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 관계 설정
    diaries = relationship("Diary", back_populates="author")
    survey_results = relationship("SurveyResult", back_populates="user")
    chat_histories = relationship("ChatHistory", back_populates="user")
   
    # 온보딩 상태
    is_onboarding_done = Column(Boolean, default=False)
    user_animal = Column(String, nullable=True)


class Diary(Base):
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    content = Column(Text)

    # 루틴 데이터
    routine_name = Column(String, nullable=True)
    is_done = Column(Boolean, default=False)

    joy = Column(Float, default=0.0)
    sadness = Column(Float, default=0.0)
    anger = Column(Float, default=0.0)
    fear = Column(Float, default=0.0)
    trust = Column(Float, default=0.0)
    disgust = Column(Float, default=0.0)
    surprise = Column(Float, default=0.0)
    anticipation = Column(Float, default=0.0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    analysis_comment = Column(String)
    
    author = relationship("User", back_populates="diaries")
    analysis_data = relationship("Analysis", back_populates="diary", uselist=False)


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    diary_id = Column(Integer, ForeignKey("diaries.id"))
    emotion = Column(String)
    score = Column(Float, default=0.0)
    feedback = Column(Text)

    diary = relationship("Diary", back_populates="analysis_data")

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    survey_type = Column(String)
    question = Column(Text)


class SurveyAnswer(Base):
    __tablename__ = "survey_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    survey_type = Column(String)
    question_id = Column(Integer)
    answer = Column(Integer)


class SurveyResult(Base):
    __tablename__ = "survey_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    survey_type = Column(String)
    score = Column(Integer)
    result = Column(String)
    user = relationship("User", back_populates="survey_results")

class ChatHistory(Base):
    __tablename__ = "chat_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String)    # "user" 또는 "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="chat_histories")