from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from pydantic import BaseModel
from services.ai_logic import analyze_diary_emotion, check_anomaly_level

class DiaryRequest(BaseModel):
    user_id: str
    content: str
    routine_name: str = None
    routine_category: str = None 
    score_diff: float = 0.0      
    is_done: bool = False        

router = APIRouter()

@router.post("/api/diary")
def create_diary(data: DiaryRequest, db: Session = Depends(get_db)):
    try:
        # [STEP 1] AI 감정 분석
        analysis = analyze_diary_emotion(data.content)
        if not analysis:
            raise HTTPException(status_code=500, detail="AI 분석 실패")

        emotions = analysis["emotions"]
        comment = analysis["analysis_comment"]

        # [STEP 2] Diary 저장 (요구사항 1, 3 반영)
        # C의 로직은 나중에 이 데이터를 user.diaries로 읽어갑니다.
        new_diary = models.Diary(
            user_id=data.user_id,
            content=data.content,
            routine_name=data.routine_name,
            routine_category=data.routine_category, 
            score_diff=data.score_diff,             
            is_done=data.is_done,
            analysis_comment=comment,
            **emotions
        )
        db.add(new_diary)
        db.flush() 

        # [STEP 3] Analysis 테이블 저장
        main_emotion = max(emotions, key=emotions.get) if emotions else "unknown"
        new_analysis = models.Analysis(
            diary_id=new_diary.id,
            emotion=main_emotion,
            score=emotions.get(main_emotion, 0.0),
            feedback=comment
        )
        db.add(new_analysis)

        # [STEP 4] 이상징후 체크를 위한 데이터 가공
        recent_diaries = db.query(models.Diary)\
            .filter(models.Diary.user_id == data.user_id)\
            .order_by(models.Diary.created_at.desc())\
            .limit(7)\
            .all()
        
        emotion_list = [{"emotions": {k: getattr(d, k) for k in emotions.keys()}} for d in recent_diaries]
        alert = check_anomaly_level(emotion_list)

        # [중요] C의 루틴 업데이트 함수 호출 삭제 (C의 코드는 DB를 직접 읽으므로 필요 없음)
        
        db.commit() 
        db.refresh(new_diary)

        return {
            "message": "저장 완료",
            "diary_id": new_diary.id,
            "alert": alert
        }
        
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=str(e))