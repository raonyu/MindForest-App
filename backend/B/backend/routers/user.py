from fastapi import APIRouter
from database import SessionLocal
import models

router = APIRouter()

@router.post("/api/signup")
def signup(id: str, password: str):
    
    db = SessionLocal()

    new_user = models.User(
        id=id,
        password=password
    )

    db.add(new_user)
    db.commit()
    db.close()

    return {"message": "signup success"}

@router.post("/api/login")
def login(id: str, password: str):

    db = SessionLocal()

    user = db.query(models.User).filter(
        models.User.id == id
    ).first()

    db.close()

    if user is None:
        return {"message" : "user not found"}
    
    if user.password != password:
        return {"message" : "password incorrect"}
    
    return {"message" : "login success"}