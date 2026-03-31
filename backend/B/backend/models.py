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
    # [수정] timezone=True 추가: 시간대 충돌 에러 방지
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # 온보딩 및 캐릭터 정보
    is_onboarding_done = Column(Boolean, default=False)
    user_animal = Column(String, nullable=True) # 예: "정리대장 펭귄"
    assigned_category = Column(String, nullable=True) # GPT가 분류한 질환 코드 (예: "OCD")

    # 관계 설정
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

    # 루틴 데이터 (담당 C 로직용)
    routine_name = Column(String, nullable=True)
    is_done = Column(Boolean, default=False)

    # 8가지 감정 수치
    joy = Column(Float, default=0.0)
    sadness = Column(Float, default=0.0)
    anger = Column(Float, default=0.0)
    fear = Column(Float, default=0.0)
    trust = Column(Float, default=0.0)
    disgust = Column(Float, default=0.0)
    surprise = Column(Float, default=0.0)
    anticipation = Column(Float, default=0.0)

    # [수정] timezone=True 추가
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    analysis_comment = Column(String)
    
    author = relationship("User", back_populates="diaries")
    # 1:1 관계 (uselist=False)
    analysis_data = relationship("Analysis", back_populates="diary", uselist=False)


# --- 3. 개별 일기 심층 분석 테이블 (마음의 가면 로직용) ---
class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    diary_id = Column(Integer, ForeignKey("diaries.id"))
    emotion = Column(String) # 주된 감정
    score = Column(Float, default=0.0) # 강도
    feedback = Column(Text)

    diary = relationship("Diary", back_populates="analysis_data")


# --- 4. 정밀 설문지 문항 테이블 ---
class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    survey_type = Column(String) # 예: "ADHD", "PHQ-9"
    question_num = Column(Integer) # 1~9번 문항 구분용
    question_text = Column(Text)


# --- 5. 사용자별 설문 답변 상세 테이블 ---
class SurveyAnswer(Base):
    __tablename__ = "survey_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    survey_type = Column(String)
    question_num = Column(Integer)
    answer = Column(Integer) # 선택한 점수 (0~3 또는 1~5)

    user = relationship("User", back_populates="survey_answers")


# --- 6. 설문 최종 결과 저장 테이블 ---
class SurveyResult(Base):
    __tablename__ = "survey_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    survey_type = Column(String)
    score = Column(Integer) # 총점
    result_message = Column(String) # "중등도 우울" 등 결과 요약
    
    # [수정] 생성일자 추가 (변화 추이 확인용)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="survey_results")


# --- 7. 챗봇 대화 이력 테이블 ---
class ChatHistory(Base):
    __tablename__ = "chat_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String)    # "user" 또는 "assistant"
    content = Column(Text)
    # [수정] timezone=True 추가
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="chat_histories")