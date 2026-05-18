from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from pydantic import BaseModel
from typing import List

router = APIRouter()

class AnimalResponse(BaseModel):
    category: str
    name: str
    emoji: str
    description: str

    class Config:
        from_attributes = True

@router.get("/all", response_model=List[AnimalResponse])
def get_all_animals(db: Session = Depends(get_db)):
    """모든 동물 정보를 가져옵니다 (동물 도감 등에서 활용)"""
    return db.query(models.Animal).all()

@router.get("/{category}", response_model=AnimalResponse)
def get_animal_by_category(category: str, db: Session = Depends(get_db)):
    """특정 카테고리의 동물 정보를 가져옵니다 (진단 결과 화면에서 활용)"""
    animal = db.query(models.Animal).filter(models.Animal.category == category.upper()).first()
    if not animal:
        raise HTTPException(status_code=404, detail="동물 정보를 찾을 수 없습니다.")
    return animal