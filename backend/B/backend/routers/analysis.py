from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import datetime
# [수정] C의 실제 파일인 routine_manager와 analysis_C 분석 함수를 임포트합니다.
import routine_manager
from services.emotion_service import get_recent_emotions
from services.ai_logic import check_anomaly_level
from services.weekly_report import build_weekly_report

router = APIRouter()

# --- [STEP 1] 특정 일기의 상세 분석 결과 조회 ---
@router.get("/api/analysis/{diary_id}")
def get_analysis(diary_id: int, db: Session = Depends(get_db)):
    """
    일기 작성 직후 또는 과거 기록 확인 시, 8종 감정 수치와 AI 코멘트를 반환합니다.
    [요구사항 반영] Diary 테이블에 추가된 루틴 카테고리와 score_diff를 결과에 포함합니다.
    """
    diary = db.query(models.Diary).filter(models.Diary.id == diary_id).first()
    
    if not diary:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
        
    return {
        "diary_id": diary.id,
        "content": diary.content,
        "routine_info": {
            "name": diary.routine_name,
            "category": diary.routine_category,  # [요구사항 1] 루틴 유형 저장 확인
            "score_diff": diary.score_diff,      # [요구사항 1] 마음 온도 변화량 확인
            "is_done": diary.is_done
        },
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
        # [요구사항 2] 가입일 계산 시 에러 없는 timezone 적용 시간
        "created_at": diary.created_at
    }

# --- [STEP 2] 사용자별 실시간 이상징후 알림 상태 조회 ---
@router.get("/api/emotion-alert/{user_id}")
def emotion_alert(user_id: str, db: Session = Depends(get_db)):
    """
    사용자의 최근 7일 감정 흐름을 분석하여 경고 레벨을 반환합니다.
    """
    recent_data = get_recent_emotions(user_id, db) 

    if not recent_data:
        return {
            "level": "LOW", 
            "message": "아직 분석할 데이터가 부족해요. 일기를 써서 마음을 기록해보세요!"
        }

    # AI 로직을 통한 상태 판정
    result = check_anomaly_level(recent_data)
    return result

# --- [STEP 3] 주간 리포트 및 맞춤형 추천 조회 (C의 로직 연동) ---
@router.get("/api/report/{user_id}")
def get_report(user_id: str, db: Session = Depends(get_db)):
    """
    [담당 C 협업] C의 실제 로직을 사용하여 주간 분석 리포트와 맞춤 루틴 추천을 생성합니다.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 1. 새 주간 리포트 엔진 호출 (카드별 상태를 따로 내려줍니다)
    try:
        weekly_report = build_weekly_report(db, user_id)
    except Exception as e:
        # 서버 오류 문구는 사용자에게 노출하지 않고 로그에만 남깁니다.
        print(f"🚨 주간 리포트 엔진 구동 실패: {e}")
        weekly_report = {
            "status": "error",
            "message": "리포트를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.",
            "cards": {}
        }

    # 2. 오늘 유저에게 할당된 추천 루틴 조회
    today = datetime.date.today()
    routines = db.query(models.UserRoutine).filter(
        models.UserRoutine.user_id == user_id,
        models.UserRoutine.date == today
    ).all()
    recommendations = [r.routine_detail.content for r in routines if r.routine_detail]
    
    # 3. 가입일 확인 (요구사항 2: signup_date)
    signup_date = user.created_at

    return {
        "user_id": user_id,
        "user_animal": user.user_animal,
        "assigned_category": user.assigned_category,
        "signup_date": signup_date,
        "weekly_report": weekly_report,  # 카드 + 상태 구조
        "recommendations": recommendations
    }
