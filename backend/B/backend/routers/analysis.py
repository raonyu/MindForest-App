from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, analysis_C
from services.emotion_service import get_recent_emotions
from services.ai_logic import check_anomaly_level

router = APIRouter()

# --- [STEP 1] 특정 일기의 상세 분석 결과 조회 ---
@router.get("/api/analysis/{diary_id}")
def get_analysis(diary_id: int, db: Session = Depends(get_db)):
    """
    일기 작성 직후 또는 과거 기록 확인 시, 8종 감정 수치와 AI 코멘트를 반환합니다.
    """
    diary = db.query(models.Diary).filter(models.Diary.id == diary_id).first()
    
    if not diary:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
        
    return {
        "diary_id": diary.id,
        "content": diary.content,
        "emotions": {
            "joy": diary.joy,
            "sadness": diary.sadness,
            "anger": diary.anger,
            "fear": diary.fear,
            "trust": diary.trust,
            "disgust": diary.disgust,
            "surprise": diary.surprise,
            "anticipation": diary.anticipation
        },
        "comment": diary.analysis_comment,
        "created_at": diary.created_at
    }

# --- [STEP 2] 사용자별 실시간 이상징후 알림 상태 조회 ---
@router.get("/api/emotion-alert/{user_id}")
def emotion_alert(user_id: str, db: Session = Depends(get_db)):
    """
    메인 화면 진입 시 사용자의 최근 7일 감정 흐름을 분석하여 경고 레벨을 알려줍니다.
    """
    # 1. 최근 감정 데이터 추출 (B의 서비스 로직 호출)
    recent_data = get_recent_emotions(user_id, db) 

    if not recent_data:
        return {
            "level": "LOW", 
            "message": "아직 분석할 데이터가 부족해요. 일기를 써서 마음을 기록해보세요!"
        }

    # 2. 이상징후 판정 (A의 AI 로직 호출)
    result = check_anomaly_level(recent_data)

    return result

# --- [STEP 3] 주간 리포트 및 맞춤형 추천 조회 ---
@router.get("/api/report/{user_id}")
def get_report(user_id: str, db: Session = Depends(get_db)):
    """
    [담당 C 협업] 지난주 대비 변화율과 질환 카테고리별 맞춤 추천을 반환합니다.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 1. C의 주간 성장률/반등지수 로직 호출
    report_res = analysis_C.get_weekly_report(db, user_id)
    
    # 2. C의 맞춤형 추천 로직 호출 (B의 필드 연동)
    # [수정] 이제 ANIMAL_MAP 없이 DB에 저장된 assigned_category를 바로 사용합니다.
    category = user.assigned_category if user.assigned_category else "DEPRESSION"
    recommendation = analysis_C.get_personalized_recommendation(category)

    return {
        "user_id": user_id,
        "user_animal": user.user_animal, # 예: "정리대장 펭귄"
        "assigned_category": category,    # 예: "OCD"
        "weekly_analysis": report_res,
        "recommendation": recommendation
    }