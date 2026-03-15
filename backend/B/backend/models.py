from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from database import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Diary(Base):
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    joy = Column(Integer)
    trust = Column(Integer)
    fear = Column(Integer)
    surprise = Column(Integer)
    sadness = Column(Integer)
    disgust = Column(Integer)
    anger = Column(Integer)
    anticipation = Column(Integer)

    analysis_comment = Column(String)


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    diary_id = Column(Integer)
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
    user_id = Column(String)
    survey_type = Column(String)
    question_id = Column(Integer)
    answer = Column(Integer)


class SurveyResult(Base):
    __tablename__ = "survey_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    survey_type = Column(String)
    score = Column(Integer)
    result = Column(String)