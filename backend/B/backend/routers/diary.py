from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db # database.py에서 정의한 함수
import models
from pydantic import BaseModel
from services.ai_logic import analyze_diary_emotion, check_anomaly_level

class DiaryRequest(BaseModel):
    user_id: str
    content: str

router = APIRouter()

@router.post("/api/diary")
def create_diary(data: DiaryRequest, db: Session = Depends(get_db)): # Depends 적용
    try:
        # 1. AI 감정 분석 호출
        analysis = analyze_diary_emotion(data.content)
        if not analysis:
            raise HTTPException(status_code=500, detail="AI 분석에 실패했습니다.")

        emotions = analysis["emotions"]
        comment = analysis["analysis_comment"]

        # 2. DB 저장 (Unpacking 활용)
        diary = models.Diary(
            user_id=data.user_id,
            content=data.content,
            analysis_comment=comment,
            **emotions # joy, sadness 등을 한 번에 매핑!
        )
        db.add(diary)
        db.commit()
        db.refresh(diary)

        # 3. 이상징후 탐지를 위한 과거 데이터 조회 (ASC 정렬)
        # A의 로직이 reversed()를 쓰므로, 여기서는 과거 -> 현재 순으로 보냅니다.
        recent_diaries = db.query(models.Diary)\
            .filter(models.Diary.user_id == data.user_id)\
            .order_by(models.Diary.created_at.asc())\
            .limit(7)\
            .all()

        emotion_list = [
            {"emotions": {"sadness": d.sadness or 0, "anger": d.anger or 0}}
            for d in recent_diaries
        ]

        # 4. 이상징후 검사
        alert = check_anomaly_level(emotion_list)

        return {
            "message": "일기 저장 및 분석 완료",
            "diary_id": diary.id,
            "analysis": analysis,
            "alert": alert
        }
    except Exception as e:
        db.rollback() # 에러 발생 시 롤백
        raise HTTPException(status_code=500, detail=str(e))