from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import datetime

import routine_manager
from analysis_C import get_mind_forest_report

from services.emotion_service import get_recent_emotions
from services.ai_logic import check_anomaly_level

# Part 2 - 개인 감정 시계열 분석
from services.emotion_trend_logic import analyze_personal_emotion_trend


router = APIRouter()


# =========================================================
# STEP 1. 특정 일기의 상세 분석 결과 조회
# =========================================================

@router.get("/api/analysis/{diary_id}")
def get_analysis(
    diary_id: int,
    db: Session = Depends(get_db),
):
    """
    일기 작성 직후 또는 과거 기록 확인 시
    8종 감정 수치와 AI 코멘트를 반환합니다.
    """

    diary = (
        db.query(models.Diary)
        .filter(models.Diary.id == diary_id)
        .first()
    )

    if not diary:
        raise HTTPException(
            status_code=404,
            detail="분석 결과를 찾을 수 없습니다.",
        )

    return {
        "diary_id": diary.id,
        "content": diary.content,

        "routine_info": {
            "name": diary.routine_name,
            "category": diary.routine_category,
            "score_diff": diary.score_diff,
            "is_done": diary.is_done,
        },

        "emotions": {
            "joy": diary.joy,
            "sadness": diary.sadness,
            "anger": diary.anger,
            "fear": diary.fear,
            "trust": diary.trust,
            "disgust": diary.disgust,
            "surprise": diary.surprise,
            "anticipation": diary.anticipation,
        },

        "comment": diary.analysis_comment,
        "created_at": diary.created_at,
    }


# =========================================================
# STEP 2. 사용자별 기존 이상징후 알림 상태 조회
# =========================================================

@router.get("/api/emotion-alert/{user_id}")
def emotion_alert(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    기존 최근 7일 감정 기반 이상징후 조회 API.
    """

    recent_data = get_recent_emotions(
        user_id,
        db,
    )

    if not recent_data:
        return {
            "level": "LOW",
            "message": (
                "아직 분석할 데이터가 부족해요. "
                "일기를 써서 마음을 기록해보세요!"
            ),
        }

    result = check_anomaly_level(
        recent_data
    )

    return result


# =========================================================
# STEP 3. Part 2 - 개인 감정 시계열 분석 API
# =========================================================

@router.get("/api/emotion-trend/{user_id}")
def get_personal_emotion_trend(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Part 2 전용 개인 감정 시계열 분석 결과를 반환합니다.

    포함:
    - 개인 기준선
    - 최근 7일 vs 개인 기준 편차
    - 변화점 탐지
    - 급격한 하락 / 레드존
    - 급락 후 회복 패턴

    LOW / MEDIUM / HIGH 최종 판단은 여기서 하지 않습니다.
    """

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="사용자를 찾을 수 없습니다.",
        )

    try:
        return analyze_personal_emotion_trend(
            db,
            user_id,
        )

    except Exception as e:
        print(
            f"[Emotion Trend Analysis Error] "
            f"user_id={user_id}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="개인 감정 추세 분석 중 오류가 발생했습니다.",
        )


# =========================================================
# STEP 4. 주간 리포트 및 맞춤형 추천 조회
# =========================================================

@router.get("/api/report/{user_id}")
def get_report(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    기존 주간 리포트와 맞춤 루틴 추천을 반환합니다.
    """

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="사용자를 찾을 수 없습니다.",
        )

    # 1. 기존 주간 분석 엔진
    try:
        report_res = get_mind_forest_report(
            db,
            user_id,
        )

        if "error" in report_res:
            report_res = {
                "status": "no_data",
                "message": (
                    "아직 주간 리포트를 분석하기에 "
                    "일기 데이터가 충분하지 않습니다."
                ),
            }

    except Exception as e:
        print(
            f"[Weekly Report Error] "
            f"user_id={user_id}: {e}"
        )

        report_res = {
            "status": "no_data",
            "message": (
                "주간 리포트를 생성하는 중 "
                "문제가 발생했습니다."
            ),
        }

    # 2. 오늘 사용자에게 할당된 추천 루틴
    today = datetime.date.today()

    routines = (
        db.query(models.UserRoutine)
        .filter(
            models.UserRoutine.user_id == user_id,
            models.UserRoutine.date == today,
        )
        .all()
    )

    recommendations = [
        routine.routine_detail.content
        for routine in routines
        if routine.routine_detail
    ]

    # 3. 최종 반환
    return {
        "user_id": user_id,
        "user_animal": user.user_animal,
        "assigned_category": user.assigned_category,
        "signup_date": user.created_at,
        "weekly_analysis": report_res,
        "recommendations": recommendations,
    }