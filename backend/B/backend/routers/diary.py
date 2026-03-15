from fastapi import APIRouter
from database import SessionLocal
import models
from pydantic import BaseModel
from services.ai_logic import analyze_diary_emotion, check_anomaly_level


class DiaryRequest(BaseModel):
    user_id: str
    content: str


router = APIRouter()


@router.post("/api/diary")
def create_diary(data: DiaryRequest):

    db = SessionLocal()

    try:
        user_id = data.user_id
        content = data.content

        # AI 감정 분석
        analysis = analyze_diary_emotion(content)

        if analysis is None:
            return {"error": "AI 감정 분석 실패"}

        emotions = analysis["emotions"]
        comment = analysis["analysis_comment"]

        # DB 저장
        diary = models.Diary(
            user_id=user_id,
            content=content,

            joy=emotions.get("joy", 0),
            trust=emotions.get("trust", 0),
            fear=emotions.get("fear", 0),
            surprise=emotions.get("surprise", 0),
            sadness=emotions.get("sadness", 0),
            disgust=emotions.get("disgust", 0),
            anger=emotions.get("anger", 0),
            anticipation=emotions.get("anticipation", 0),

            analysis_comment=comment
        )

        db.add(diary)
        db.commit()
        db.refresh(diary)

        # 최근 7개 감정 조회
        recent_diaries = db.query(models.Diary)\
            .filter(models.Diary.user_id == user_id)\
            .order_by(models.Diary.created_at.desc())\
            .limit(7)\
            .all()

        emotion_list = []

        for d in recent_diaries:
            emotion_list.append({
                "emotions": {
                    "sadness": d.sadness or 0,
                    "anger": d.anger or 0
                }
            })

        # 이상징후 검사
        alert = check_anomaly_level(emotion_list)

        return {
            "message": "일기 저장 완료",
            "analysis": analysis,
            "alert": alert
        }

    finally:
        db.close()


@router.get("/api/diary/{user_id}")
def get_diaries(user_id: str):

    db = SessionLocal()

    try:
        diaries = db.query(models.Diary).filter(
            models.Diary.user_id == user_id
        ).all()

        return diaries

    finally:
        db.close()