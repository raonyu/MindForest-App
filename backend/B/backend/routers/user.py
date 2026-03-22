from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt  # passlib 대신 bcrypt 직접 사용
from database import get_db
import models
from pydantic import BaseModel

class UserAuth(BaseModel):
    id: str
    password: str

router = APIRouter()

# --- [B의 현대적인 해싱 로직] ---
def get_password_hash(password: str):
    # 비밀번호를 바이트로 변환 후 솔트(Salt)와 함께 해싱
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8') # DB 저장을 위해 문자열로 변환

def verify_password(plain_password: str, hashed_password: str):
    # 입력받은 비밀번호와 DB의 해시값을 비교
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)
# ------------------------------

@router.post("/api/signup")
def signup(data: UserAuth, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.id == data.id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    # 새로운 해싱 함수 사용
    hashed_password = get_password_hash(data.password)
    new_user = models.User(
        id=data.id,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    return {"message": "signup success"}

@router.post("/api/login")
def login(data: UserAuth, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.id).first()
    
    # 새로운 검증 함수 사용
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")
    
    return {"message": "login success", "user_id": user.id}