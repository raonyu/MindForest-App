from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    diaries = relationship("Diary", back_populates="author")
    survey_results = relationship("SurveyResult", back_populates="user")
    chat_histories = relationship("ChatHistory", back_populates="user")
    is_onboarding_done = Column(Boolean, default=False)
    user_animal = Column(String, nullable=True)


class Diary(Base):
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    joy = Column(Integer)
    trust = Column(Integer)
    fear = Column(Integer)
    surprise = Column(Integer)
    sadness = Column(Integer)
    disgust = Column(Integer)
    anger = Column(Integer)
    anticipation = Column(Integer)

    analysis_comment = Column(String)

    author = relationship("User", back_populates="diaries")


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    diary_id = Column(Integer, ForeignKey("diaries.id"))
    emotion = Column(String)
    score = Column(Integer)
    feedback = Column(Text)


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