from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, analysis_C
from services.emotion_service import get_recent_emotions
from services.ai_logic import check_anomaly_level

router = APIRouter()

ANIMAL_MAP = {
    "조용히 숨 고르는 거북이": "A",
    "볼이 빵빵한 화난 햄스터": "H",
    "도토리 찾는 꼬마 다람쥐": "I",
    # ... 나머지 동물들도 추가
}

# 1. 특정 일기의 상세 분석 결과 조회
@router.get("/api/analysis/{diary_id}")
def get_analysis(diary_id: int, db: Session = Depends(get_db)):
    # models.Analysis 대신 Diary 테이블에서 바로 가져오는 것이 효율적일 수 있습니다.
    result = db.query(models.Diary).filter(models.Diary.id == diary_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
        
    return {
        "diary_id": result.id,
        "emotions": {
            "joy": result.joy, "sadness": result.sadness, # ... 나머지 감정들
        },
        "comment": result.analysis_comment
    }

# 2. 사용자별 이상징후 알림 상태 조회 (메인 기능)
@router.get("/api/emotion-alert/{user_id}")
def emotion_alert(user_id: str, db: Session = Depends(get_db)):
    # [Step 1] 서비스 함수 호출 (B가 만든 로직)
    # 주의: get_recent_emotions 함수가 db 세션을 인자로 받도록 수정되어야 합니다.
    recent_data = get_recent_emotions(user_id, db) 

    if not recent_data:
        return {"level": "LOW", "message": "최근 분석 데이터가 충분하지 않습니다."}

    # [Step 2] 이상징후 판정 (A가 만든 로직)
    result = check_anomaly_level(recent_data)

    return result

@router.get("/api/report/{user_id}")
def get_report(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    # 1. C의 get_weekly_report 호출 (C의 요구대로 db 세션을 그대로 전달)
    report_res = analysis_C.get_weekly_report(db, user_id)
    
    # 2. C의 get_personalized_recommendation 호출을 위한 매핑 (B의 센스!)
    full_name = user.user_animal if user else ""
    short_type = ANIMAL_MAP.get(full_name, "Unknown") # 풀네임을 A, H 등으로 변환
    
    recommendation = analysis_C.get_personalized_recommendation(short_type)

    return {
        "analysis": report_res,
        "recommendation": recommendation,
        "user_animal": full_name
    }