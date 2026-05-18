from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from routine_manager import routine_manager

router = APIRouter()

@router.get("/today/{user_id}")
def get_my_routines(user_id: str, db: Session = Depends(get_db)):
    """오늘 나에게 할당된 루틴 목록을 가져옵니다."""
    routines = routine_manager.get_daily_recommendations(db, user_id)
    return [
        {
            "user_routine_id": r.id,
            "content": r.routine_detail.content,
            "is_completed": r.is_completed,
            "level": r.routine_detail.level
        } for r in routines
    ]

@router.get("/master/all")
def get_all_master_routines(db: Session = Depends(get_db)):
    """
    DB에 저장된 모든 루틴 마스터 데이터(27개)를 가져옵니다.
    (루틴 도감이나 관리용으로 사용)
    """
    routines = db.query(models.RoutineMaster).all()
    
    result = {}
    for r in routines:
        if r.category not in result:
            result[r.category] = []
        result[r.category].append({
            "level": r.level,
            "content": r.content
        })
    
    return result

@router.patch("/complete/{user_routine_id}")
def complete_routine(user_routine_id: int, db: Session = Depends(get_db)):
    """루틴 완료 체크를 수행합니다."""
    routine = db.query(models.UserRoutine).filter(models.UserRoutine.id == user_routine_id).first()
    if not routine:
        raise HTTPException(status_code=404, detail="루틴을 찾을 수 없습니다.")
    
    routine.is_completed = True
    db.commit()
    return {"message": "routine completed!"}