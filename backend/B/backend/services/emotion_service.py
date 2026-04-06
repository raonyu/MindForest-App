from sqlalchemy.orm import Session
from services.ai_logic import analyze_diary_emotion, check_anomaly_level
import models
# [수정] C의 실제 파일명에 맞춰 임포트 (analysis_C가 없다면 삭제 가능)
import routine_manager, analysis_C
from datetime import datetime, timezone

def get_recent_emotions(user_id: str, db: Session):
    """
    [담당 B/C 협업] 최근 7일치의 감정 데이터를 추출합니다.
    - [요구사항 2 반영] models.py의 timezone=True 설정을 활용해 Pandas 연산 시 안전하도록 처리합니다.
    """
    try:
        # 1. 최신순(desc)으로 최근 7개를 가져옵니다.
        subquery = db.query(models.Diary)\
            .filter(models.Diary.user_id == user_id)\
            .order_by(models.Diary.created_at.desc())\
            .limit(7)\
            .all()

        # 2. 시간대 충돌 방지 정렬 (models.py의 timezone=True 덕분에 안전합니다)
        recent_diaries = sorted(
            subquery, 
            key=lambda x: x.created_at.replace(tzinfo=timezone.utc) if x.created_at.tzinfo is None else x.created_at
        )

        result = []
        for d in recent_diaries:
            result.append({
                "created_at": d.created_at,
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

def process_diary_and_check_anomaly(
    user_id: str, 
    diary_text: str, 
    routine_name: str, 
    routine_category: str, # [요구사항 1/3]
    score_diff: float,      # [요구사항 1/3]
    is_done: bool, 
    db: Session
):
    """
    [담당 B] 일기 저장, 감정 분석, 이상징후 체크
    [핵심 수정] 조원 C의 코드는 DB를 직접 읽으므로, 별도의 업데이트 함수 호출을 제거했습니다.
    """
    # [Step 1] AI 분석 (담당 A의 함수 호출)
    analysis_result = analyze_diary_emotion(diary_text)
    if not analysis_result:
        return None 

    emotions = analysis_result['emotions']
    comment = analysis_result['analysis_comment']

    # [Step 2] 일기(Diary) 데이터 저장 (루틴 신규 필드 포함)
    # [요구사항 3 반영] 이 데이터가 DB에 들어가야 C의 routine_manager가 분석할 수 있습니다.
    new_diary = models.Diary(
        user_id=user_id,
        content=diary_text,
        routine_name=routine_name,
        routine_category=routine_category, # 저장!
        score_diff=score_diff,             # 저장!
        is_done=is_done,
        analysis_comment=comment,
        **emotions
    )
    db.add(new_diary)
    db.flush() # ID 생성을 위해 flush

    # [Step 3] 심층 분석(Analysis) 데이터 저장
    main_emotion = max(emotions, key=emotions.get) if emotions else "unknown"
    ai_score = emotions.get(main_emotion, 0.0)

    new_analysis = models.Analysis(
        diary_id=new_diary.id,
        emotion=main_emotion,
        score=ai_score,
        feedback=comment
    )
    db.add(new_analysis)

    # [Step 4] 이상징후 체크
    recent_data = get_recent_emotions(user_id, db) 
    anomaly_status = check_anomaly_level(recent_data)
    
    # [수정 포인트] routine_manager.update_routine_status 호출 삭제!
    # C의 로직(get_recommended_routines)은 DB에 저장된 diaries를 직접 조회하므로
    # 아래의 db.commit()만 성공하면 C의 로직과 연동이 끝난 것입니다.

    # 최종 커밋
    try:
        db.commit()
        db.refresh(new_diary)
    except Exception as e:
        db.rollback()
        print(f"DB Commit Error: {e}")
        return None

    return {
        "diary_id": new_diary.id,
        "routine_category": new_diary.routine_category,
        "score_diff": new_diary.score_diff,
        "emotions": emotions,
        "analysis_comment": comment,
        "alert": anomaly_status
    }