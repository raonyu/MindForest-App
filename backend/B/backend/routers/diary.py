from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from database import get_db
import models
from pydantic import BaseModel
from services.ai_logic import analyze_diary_emotion, check_anomaly_level
from datetime import datetime

# --- [1. 요청 데이터 모델] ---
class DiaryRequest(BaseModel):
    user_id: str
    content: str
    date: str = None  # 신규: "2026-05-06" (없으면 오늘 날짜)
    emotion: str = None  # 신규: 프론트에서 선택한 대표 감정
    routine_name: str = None
    routine_category: str = None 
    score_diff: float = 0.0      
    is_done: bool = False        

router = APIRouter()

# --- [2. 일기 저장 및 수정 (POST)] ---
@router.post("")
def create_or_update_diary(data: DiaryRequest, db: Session = Depends(get_db)):
    try:
        # 1. 날짜 처리 (프론트에서 항상 YYYY-MM-DD 형식으로 옴)
        if data.date:
            target_date = datetime.strptime(data.date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()

        # 2. AI 감정 분석 (기존 로직 유지)
        analysis = analyze_diary_emotion(data.content)
        if not analysis:
            raise HTTPException(status_code=500, detail="AI 분석 실패")

        emotions = analysis["emotions"]
        comment = analysis["analysis_comment"]

        # 3. 해당 날짜에 이미 일기가 있는지 확인 (Upsert 로직)
        existing_diary = db.query(models.Diary).filter(
            models.Diary.user_id == data.user_id,
            func.date(models.Diary.created_at) == target_date
        ).first()

        if existing_diary:
            # [Update] 기존 데이터 덮어쓰기
            existing_diary.content = data.content
            existing_diary.emotion = data.emotion or existing_diary.emotion
            existing_diary.routine_name = data.routine_name or existing_diary.routine_name
            existing_diary.routine_category = data.routine_category or existing_diary.routine_category
            existing_diary.score_diff = data.score_diff
            existing_diary.is_done = data.is_done
            existing_diary.analysis_comment = comment
            # 감정 점수 업데이트
            for k, v in emotions.items():
                setattr(existing_diary, k, v)
            new_diary = existing_diary
        else:
            # [Insert] 신규 저장
            new_diary = models.Diary(
                user_id=data.user_id,
                content=data.content,
                emotion=data.emotion,
                routine_name=data.routine_name,
                routine_category=data.routine_category,
                score_diff=data.score_diff,
                is_done=data.is_done,
                analysis_comment=comment,
                created_at=datetime.combine(target_date, datetime.now().time()),
                **emotions
            )
            db.add(new_diary)
        
        db.flush() 

        # 4. Analysis 테이블 저장 (기존 로직 유지)
        main_emotion = data.emotion if data.emotion else (max(emotions, key=emotions.get) if emotions else "unknown")
        new_analysis = models.Analysis(
            diary_id=new_diary.id,
            emotion=main_emotion,
            score=emotions.get(main_emotion, 0.0),
            feedback=comment
        )
        db.add(new_analysis)

        # 5. 이상징후 체크 (기존 로직 유지)
        recent_diaries = db.query(models.Diary)\
            .filter(models.Diary.user_id == data.user_id)\
            .order_by(models.Diary.created_at.desc())\
            .limit(7)\
            .all()
        
        emotion_list = [{"emotions": {k: getattr(d, k, 0.0) for k in emotions.keys()}} for d in recent_diaries]
        alert = check_anomaly_level(emotion_list)

        db.commit()
        db.refresh(new_diary)

        return {
            "status": "success",
            "diary_id": new_diary.id,
            "alert": alert
        }
        
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=str(e))

# --- [3. 월별 일기 불러오기 (GET)] ---
@router.get("/monthly")
def get_monthly_diaries(
    user_id: str, 
    year: int = Query(..., example=2026), 
    month: int = Query(..., example=5), 
    db: Session = Depends(get_db)
):
    diaries = db.query(models.Diary).filter(
        models.Diary.user_id == user_id,
        extract('year', models.Diary.created_at) == year,
        extract('month', models.Diary.created_at) == month
    ).order_by(models.Diary.created_at.asc()).all()

    return {
        "data": [
            {
                "date": d.created_at.strftime("%Y-%m-%d"),
                "emotion": getattr(d, 'emotion', "joy"), # 필드명 확인 필요
                "content": d.content
            } for d in diaries
        ]
    }

# --- [4. 특정 일기 삭제 (DELETE)] ---
@router.delete("")
def delete_diary(user_id: str, date: str, db: Session = Depends(get_db)):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다.")

    # 해당 날짜의 일기 찾기
    diary_to_delete = db.query(models.Diary).filter(
        models.Diary.user_id == user_id,
        func.date(models.Diary.created_at) == target_date
    ).first()

    if not diary_to_delete:
        raise HTTPException(status_code=404, detail="해당 날짜의 일기가 없습니다.")

    # Analysis 등 연관 데이터는 DB의 On Delete Cascade 설정에 따라 자동 삭제되거나, 
    # 여기서 수동으로 삭제해야 할 수 있습니다.
    db.delete(diary_to_delete)
    db.commit()
    
    return {"status": "success"}