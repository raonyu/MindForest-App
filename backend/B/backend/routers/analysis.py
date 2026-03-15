from fastapi import APIRouter
from database import SessionLocal
import models
from pydantic import BaseModel
from services.emotion_service import get_recent_emotions
from services.ai_logic import check_anomaly_level


router = APIRouter()


class AnalysisRequest(BaseModel):
    diary_id: int
    emotion: str
    score: int
    feedback: str


@router.post("/api/analysis")
def save_analysis(data: AnalysisRequest):

    db = SessionLocal()

    try:
        new_analysis = models.Analysis(
            diary_id=data.diary_id,
            emotion=data.emotion,
            score=data.score,
            feedback=data.feedback
        )

        db.add(new_analysis)
        db.commit()

        return {"message": "analysis saved"}

    finally:
        db.close()


@router.get("/api/analysis/{diary_id}")
def get_analysis(diary_id: int):

    db = SessionLocal()

    try:
        result = db.query(models.Analysis).filter(
            models.Analysis.diary_id == diary_id
        ).first()

        return result

    finally:
        db.close()


@router.get("/api/emotion-alert/{user_id}")
def emotion_alert(user_id: str):

    recent_data = get_recent_emotions(user_id)

    result = check_anomaly_level(recent_data)

    return result