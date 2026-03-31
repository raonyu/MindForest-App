from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt
from database import get_db
import models
from pydantic import BaseModel
from services.ai_logic import analyze_onboarding_survey  # AI 분석 함수 임입

# --- [1. 요청 데이터 모델] ---
class UserAuth(BaseModel):
    id: str
    password: str

class OnboardingRequest(BaseModel):
    user_id: str
    responses: str  # "1. 예, 2. 아니오..." 혹은 질문-답변 텍스트 전체

# --- [2. 라우터 설정] ---
router = APIRouter()

# --- [3. 보안 로직 (B의 해싱)] ---
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
    new_user = models.User(
        id=data.id,
        password=hashed_password,
        is_onboarding_done=False  # 초기값 설정
    )

    db.add(new_user)
    db.commit()
    return {"message": "signup success"}


# --- [5. 로그인 엔드포인트] ---
@router.post("/api/login")
def login(data: UserAuth, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.id).first()
    
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")
    
    return {
        "message": "login success", 
        "user_id": user.id,
        "is_onboarding_done": user.is_onboarding_done,
        "user_animal": user.user_animal
    }


# --- [6. 온보딩 분석 및 캐릭터 배정 엔드포인트] ---
@router.post("/api/user/onboarding")
def complete_onboarding(data: OnboardingRequest, db: Session = Depends(get_db)):
    """
    사용자의 20문항 답변을 받아 GPT로 분석하고, 
    9가지 질환 중 하나를 배정하여 동물 캐릭터를 부여합니다.
    """
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 1. GPT를 통한 온보딩 설문 분석 호출
    analysis_result = analyze_onboarding_survey(data.responses)
    
    if not analysis_result:
        raise HTTPException(status_code=500, detail="온보딩 분석에 실패했습니다.")

    # 2. 분석 결과 DB 업데이트
    user.assigned_category = analysis_result["category"]  # 예: "ADHD"
    user.user_animal = analysis_result["name"]            # 예: "산만한 꼬마 다람쥐"
    user.is_onboarding_done = True
    
    db.commit()
    db.refresh(user)

    # 3. 프론트엔드에 캐릭터 정보와 다음에 진행할 정밀 설문지 정보 전달
    return {
        "message": "onboarding complete",
        "user_animal": user.user_animal,
        "assigned_category": user.assigned_category,
        "next_survey": analysis_result["survey"],  # 예: "ASRS"
        "reason": analysis_result["reason"]
    }