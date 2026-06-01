from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
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
    
    # [동기화] 오늘 작성된 일기(Diary)가 있다면, 일기 테이블 내 루틴 완료 관련 필드도 자동으로 동기화합니다.
    today_date = routine.date
    existing_diary = db.query(models.Diary).filter(
        models.Diary.user_id == routine.user_id,
        func.date(models.Diary.created_at) == today_date
    ).first()
    
    if existing_diary:
        existing_diary.routine_name = routine.routine_detail.content if routine.routine_detail else None
        existing_diary.routine_category = routine.routine_detail.category if routine.routine_detail else None
        existing_diary.is_done = True
        existing_diary.score_diff = 10.0

    db.commit()
    return {"message": "routine completed!"}