from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
# [수정] C의 실제 파일인 routine_manager를 임포트합니다.
import routine_manager 
from services.emotion_service import get_recent_emotions
from services.ai_logic import check_anomaly_level

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
    
    # 1. C의 분석 함수(analyze_routine_logs)를 위한 데이터 가공
    # DB에 저장된 user.diaries 데이터를 C가 요구하는 딕셔너리 리스트 형태로 변환합니다.
    logs = [
        {
            "category": d.routine_category,
            "score_diff": d.score_diff if d.score_diff else 0.0,
            "is_completed": d.is_done
        }
        for d in user.diaries
    ]
    
    # C의 분석 로직 호출
    report_res = routine_manager.analyze_routine_logs(logs)
    
    # 2. C의 추천 로직(get_recommended_routines) 호출
    # user 객체를 통째로 넘기면 C의 함수가 내부에서 가입일과 일기 목록을 분석합니다.
    recommendations = routine_manager.get_recommended_routines(user)
    
    # 3. 가입일 확인 (요구사항 2: signup_date)
    signup_date = user.created_at

    return {
        "user_id": user_id,
        "user_animal": user.user_animal,
        "assigned_category": user.assigned_category,
        "signup_date": signup_date,
        "weekly_analysis": report_res,   # C의 analyze_routine_logs 결과
        "recommendations": recommendations # C의 get_recommended_routines 결과
    }