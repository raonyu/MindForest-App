from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt
from database import get_db
import models
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
import datetime

# 서비스 로직 임포트 (경로를 본인 환경에 맞게 확인하세요)
import routine_manager
from services.chatbot_logic import get_chat_response

router = APIRouter()

class UserAuth(BaseModel):
    id: str
    password: str

class OnboardingRequest(BaseModel):
    user_id: str
    responses: List[str]

# --- [비밀번호 보안] ---
def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- [회원가입 / 로그인] ---
@router.post("/signup")
def signup(data: UserAuth, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.id == data.id).first():
        raise HTTPException(status_code=400, detail="중복 아이디")
    new_user = models.User(id=data.id, password=get_password_hash(data.password))
    db.add(new_user)
    db.commit()
    return {"message": "signup success"}

@router.post("/login")
def login(data: UserAuth, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.id).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="로그인 실패")
    return {"message": "login success", "user_id": user.id, "is_onboarding_done": user.is_onboarding_done}

# --- [온보딩 완료 및 동물 배정 - 핵심 로직] ---
@router.post("/onboarding")
def complete_onboarding(data: OnboardingRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 1. AI 분석 (결과 예: DEPRESSION)
    chat_history = [{"role": "user", "content": res} for res in data.responses]
    analysis = get_chat_response("분석해줘", chat_history=chat_history, is_onboarding_done=False)
    
    # 2. 카테고리 코드 세척
    category_code = str(analysis["category"]).strip().upper()

    # 3. [핵심] DB의 Animal 테이블에서 실제 이름을 가져옴
    animal_info = db.query(models.Animal).filter(models.Animal.category == category_code).first()
    
    # 4. 유저 테이블에 즉시 기록 (이게 되어야 Profile에서 null이 안 나옴)
    user.assigned_category = category_code
    if animal_info:
        user.user_animal = animal_info.name  # 예: "느긋한 거북이"
    else:
        user.user_animal = f"신비로운 {category_code}" # DB에 없을 때 방어코드

    user.is_onboarding_done = True
    
    # 5. 루틴 데이터도 이때 생성해버림
    try:
        routine_manager.initialize_user_routine(db, user.id, category_code)
    except Exception as e:
        print(f"루틴 할당 실패: {e}")

    # 6. DB에 최종 커밋 (확정 저장)
    db.commit()
    db.refresh(user)

    return {
        "status": "success", 
        "animal_category": user.user_animal, # 요청하신 이름으로 반환
        "category_code": user.assigned_category
    }

# --- [프로필 조회: 온보딩에서 저장한 값을 그대로 가져옴] ---
@router.get("/profile/{user_id}")
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    # 1. 저장된 카테고리를 기반으로 동물 상세 정보 실시간 매핑
    animal_info = db.query(models.Animal).filter(
        models.Animal.category == user.assigned_category
    ).first()

    # 2. 전문 진단 결과 조회
    latest_survey = db.query(models.SurveyResult).filter(
        models.SurveyResult.user_id == user_id,
        models.SurveyResult.survey_type == user.assigned_category
    ).order_by(models.SurveyResult.created_at.desc()).first()

    # 3. 오늘 할당된 루틴 조회
    today = datetime.date.today()
    routines = db.query(models.UserRoutine).filter(
        models.UserRoutine.user_id == user_id, 
        models.UserRoutine.date == today
    ).all()

    routine_list = []
    for r in routines:
        routine_list.append({
            "user_routine_id": r.id,
            "content": r.routine_detail.content if r.routine_detail else "내용 없음",
            "is_completed": r.is_completed
        })

    return {
        "user_id": user.id,
        "is_onboarding_done": user.is_onboarding_done,
        "assigned_category": user.assigned_category,
        "animal_category": animal_info.name if animal_info else user.user_animal,
        "animal_emoji": animal_info.emoji if animal_info else "🐾",
        "animal_description": animal_info.description if animal_info else "분석 완료",
        "diagnosis_result": {
            "total_score": latest_survey.score if latest_survey else 0,
            "result_message": latest_survey.result_message if latest_survey else "기록 없음"
        },
        "today_routines": routine_list  # [수정] 3개가 모두 담겨서 나갑니다.
    }