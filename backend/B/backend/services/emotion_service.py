from database import SessionLocal
import models
from datetime import datetime, timedelta


def get_recent_emotions(user_id):

    db = SessionLocal()

    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        diaries = db.query(models.Diary).filter(
            models.Diary.user_id == user_id,
            models.Diary.created_at >= seven_days_ago
        ).order_by(models.Diary.created_at).all()

        result = []

        for d in diaries:
            result.append({
                "emotions": {
                    "joy": d.joy or 0,
                    "trust": d.trust or 0,
                    "fear": d.fear or 0,
                    "surprise": d.surprise or 0,
                    "sadness": d.sadness or 0,
                    "disgust": d.disgust or 0,
                    "anger": d.anger or 0,
                    "anticipation": d.anticipation or 0
                }
            })

        return result

    finally:
        db.close()