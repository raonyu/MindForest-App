from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt
from database import get_db
import models
# [추가] 조원 C의 루틴 관리 로직 연동
import routine_manager
from pydantic import BaseModel
from services.ai_logic import analyze_onboarding_survey
from datetime import datetime

# --- [1. 요청 데이터 모델] ---
class UserAuth(BaseModel):
    id: str
    password: str

class OnboardingRequest(BaseModel):
    user_id: str
    responses: str  # 질문-답변 텍스트 전체

# --- [2. 라우터 설정] ---
router = APIRouter()

# --- [3. 보안 로직] ---
def get_password_hash(password: str):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# --- [4. 회원가입 엔드포인트] ---
@router.post("/api/signup")
def signup(data: UserAuth, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.id == data.id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    hashed_password = get_password_hash(data.password)
    
    # [요구사항 2 반영] created_at(가입일)은 models.py에서 DateTime(timezone=True)로 설정됨
    new_user = models.User(
        id=data.id,
        password=hashed_password,
        is_onboarding_done=False
    )

    db.add(new_user)
    db.commit()
    return {"message": "signup success", "signup_date": new_user.created_at}


# --- [5. 로그인 엔드포인트] ---
@router.post("/api/login")
def login(data: UserAuth, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.id).first()
    
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")
    
    # [요구사항 2 반영] 가입일(signup_date) 정보를 함께 반환하여 프론트/분석에서 활용
    return {
        "message": "login success", 
        "user_id": user.id,
        "is_onboarding_done": user.is_onboarding_done,
        "user_animal": user.user_animal,
        "signup_date": user.created_at  # timezone-aware datetime
    }


# --- [6. 온보딩 분석 및 캐릭터 배정 엔드포인트] ---
@router.post("/api/user/onboarding")
def complete_onboarding(data: OnboardingRequest, db: Session = Depends(get_db)):
    """
    GPT 분석 후 질환 카테고리를 배정하고, C의 로직을 통해 첫 루틴을 할당합니다.
    """
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 1. GPT를 통한 온보딩 설문 분석
    analysis_result = analyze_onboarding_survey(data.responses)
    
    if not analysis_result:
        raise HTTPException(status_code=500, detail="온보딩 분석에 실패했습니다.")

    # 2. 분석 결과 DB 업데이트
    user.assigned_category = analysis_result["category"]  # 예: "ADHD"
    user.user_animal = analysis_result["name"]            # 예: "산만한 다람쥐"
    user.is_onboarding_done = True
    
    # 3. [C의 협업 포인트] 온보딩 완료 즉시 해당 카테고리에 맞는 초기 루틴 생성
    # routine_manager.py의 로직을 호출하여 사용자의 첫 루틴 데이터를 세팅합니다.
    try:
        routine_manager.initialize_user_routine(
            user_id=user.id, 
            category=user.assigned_category
        )
    except Exception as e:
        print(f"루틴 초기화 경고: {e}") # 루틴 초기화 실패가 회원가입 실패로 이어지진 않게 처리

    db.commit()
    db.refresh(user)

    return {
        "message": "onboarding complete",
        "user_animal": user.user_animal,
        "assigned_category": user.assigned_category,
        "signup_date": user.created_at, # 요구사항 2 반영
        "next_survey": analysis_result["survey"],
        "reason": analysis_result["reason"]
    }