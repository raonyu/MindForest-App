from sqlalchemy.orm import Session
from .ai_logic import analyze_diary_emotion, check_anomaly_level
import models
from datetime import datetime, timedelta, timezone

def get_recent_emotions(user_id: str, db: Session):
    """
    [담당 B] 최근 7일치(혹은 최근 7개)의 감정 데이터를 안전하게 추출합니다.
    - 시간대 충돌 방지 및 최신 데이터 우선 추출 로직 적용
    """
    try:
        # 1. 최신순(desc)으로 최근 7개를 가져옵니다.
        subquery = db.query(models.Diary)\
            .filter(models.Diary.user_id == user_id)\
            .order_by(models.Diary.created_at.desc())\
            .limit(7)\
            .all()

        # 2. 시간대(naive vs aware) 충돌을 방지하며 다시 시간순(asc)으로 정렬합니다.
        # DB의 created_at에 timezone=True가 설정되어 있어야 합니다.
        recent_diaries = sorted(
            subquery, 
            key=lambda x: x.created_at.replace(tzinfo=timezone.utc) if x.created_at.tzinfo is None else x.created_at
        )

        result = []
        for d in recent_diaries:
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

    except Exception as e:
        print(f"Error in get_recent_emotions: {e}")
        return []

def process_diary_and_check_anomaly(user_id: str, diary_text: str, routine_name: str, is_done: bool, db: Session):
    """
    [담당 B] 일기 저장, 감정 분석, 이상징후 체크를 한 번에 처리하는 핵심 서비스 로직
    """
    # [Step 1] AI 분석 (담당 A의 함수 호출)
    analysis_result = analyze_diary_emotion(diary_text)
    if not analysis_result:
        return None 

    emotions = analysis_result['emotions']
    comment = analysis_result['analysis_comment']

    # [Step 2] 일기(Diary) 데이터 저장 (루틴 정보 포함)
    new_diary = models.Diary(
        user_id=user_id,
        content=diary_text,
        routine_name=routine_name,
        is_done=is_done,
        analysis_comment=comment,
        **emotions
    )
    db.add(new_diary)
    db.flush() # Analysis 테이블 연동을 위해 ID 생성

    # [Step 3] 심층 분석(Analysis) 데이터 저장 (담당 C의 '마음의 가면' 로직용)
    main_emotion = max(emotions, key=emotions.get) if emotions else "unknown"
    ai_score = emotions.get(main_emotion, 0.0)

    new_analysis = models.Analysis(
        diary_id=new_diary.id,
        emotion=main_emotion,
        score=ai_score,
        feedback=comment
    )
    db.add(new_analysis)

    # [Step 4] 이상징후 체크 (최근 7일치 데이터 기반)
    # 위에서 작성한 get_recent_emotions 함수 활용
    recent_data = get_recent_emotions(user_id, db) 
    anomaly_status = check_anomaly_level(recent_data)

    # 최종 커밋 (모든 작업이 성공했을 때만)
    try:
        db.commit()
        db.refresh(new_diary)
    except Exception as e:
        db.rollback()
        print(f"DB Commit Error: {e}")
        return None

    return {
        "diary_id": new_diary.id,
        "emotions": emotions,
        "analysis_comment": comment,
        "alert": anomaly_status
    }