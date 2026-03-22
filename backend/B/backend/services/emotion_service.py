from database import SessionLocal
from .ai_logic import analyze_diary_emotion, check_anomaly_level
from sqlalchemy.orm import Session
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

def process_diary_and_check_anomaly(user_id: str, diary_text: str, db: Session):
    # [Step 1] AI 분석 (담당 A의 함수 호출)
    analysis_result = analyze_diary_emotion(diary_text)
    if not analysis_result:
        return None # 에러 처리

    # [Step 2] 분석 결과 DB 저장 (B의 영역)
    new_diary = models.Diary(
        user_id=user_id,
        content=diary_text,
        **analysis_result['emotions'], # 감정 수치 언패킹
        analysis_comment=analysis_result['analysis_comment']
    )
    db.add(new_diary)
    db.commit()

    # [Step 3] 이상징후 체크 (담당 A의 함수 호출)
    # 최근 7일치 데이터를 가져오는 B의 함수 호출 (이전에 만든 것)
    recent_data = get_recent_emotions(user_id, db) 
    anomaly_status = check_anomaly_level(recent_data)

    return {
        "diary_id": new_diary.id,
        "emotions": analysis_result['emotions'],
        "anomaly": anomaly_status # 이 정보로 프론트에서 팝업을 띄움
    }