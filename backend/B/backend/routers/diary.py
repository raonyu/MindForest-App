import json
from datetime import datetime, timezone
from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel

from database import get_db, SessionLocal
import models
import routine_manager

# C 개발용 Mock 분석기
# 나중에 B의 실제 emotion_pipeline으로 import만 교체
from services.mock_emotion_pipeline import analyze_emotion_pipeline


router = APIRouter()


# AI가 출력하는 Plutchik 8감정
EMOTION_KEYS = [
    "joy",
    "trust",
    "fear",
    "surprise",
    "sadness",
    "disgust",
    "anger",
    "anticipation",
]


# =========================================================
# 요청 모델
# =========================================================

class DiaryRequest(BaseModel):
    user_id: str
    date: Optional[str] = None

    # 사용자 Self-Report 1순위 감정
    emotion: Optional[str] = None
    emotion_intensity: Optional[int] = None

    # 사용자 Self-Report 2순위 감정
    secondary_emotion: Optional[str] = None
    secondary_emotion_intensity: Optional[int] = None

    # 일기 데이터
    main_text: str = ""
    bg_color_id: str = "#ffffff"
    font: str = "System"
    elements: List[Any] = []

    # 기존 루틴 데이터
    routine_name: Optional[str] = None
    routine_category: Optional[str] = None
    score_diff: float = 0.0
    is_done: bool = False

    # 구버전 프론트 호환용
    content: Optional[str] = None


class RoutineRequest(BaseModel):
    user_id: str
    routine_name: str
    is_done: bool


# =========================================================
# 백그라운드 AI 감정 분석
# =========================================================

def run_emotion_analysis(
    diary_id: int,
    analysis_version: int,
    diary_text: str,
):
    """
    일기 저장 응답이 끝난 뒤 백그라운드에서 실행된다.

    중요:
    요청에서 사용한 db Session을 재사용하지 않고
    여기서 새로운 SessionLocal을 연다.
    """

    db = SessionLocal()

    try:
        # 현재는 Mock
        # 나중에 B의 실제 analyze_emotion_pipeline()으로 교체
        result = analyze_emotion_pipeline(diary_text)

        diary = (
            db.query(models.Diary)
            .filter(models.Diary.id == diary_id)
            .first()
        )

        # 사용자가 분석 도중 일기를 삭제한 경우
        if diary is None:
            return

        # 사용자가 분석 도중 일기를 다시 수정했다면
        # 오래된 분석 결과는 저장하지 않는다.
        if diary.analysis_version != analysis_version:
            return

        emotions = result.get("emotions", {})

        # 8감정 저장
        for emotion_name in EMOTION_KEYS:
            value = emotions.get(emotion_name, 0.0)

            try:
                value = float(value)
            except (TypeError, ValueError):
                value = 0.0

            setattr(diary, emotion_name, value)

        # 분석 부가정보 저장
        diary.confidence = result.get("confidence")
        diary.bws_used = bool(result.get("bws_used", False))
        diary.analysis_status = "completed"
        diary.analysis_completed_at = datetime.now(timezone.utc)

        # 기존 Analysis 테이블과도 호환
        if emotions:
            main_emotion = max(
                EMOTION_KEYS,
                key=lambda key: float(emotions.get(key, 0.0))
            )
            main_score = float(emotions.get(main_emotion, 0.0))
        else:
            main_emotion = "unknown"
            main_score = 0.0

        analysis_comment = result.get("analysis_comment", "")

        existing_analysis = (
            db.query(models.Analysis)
            .filter(models.Analysis.diary_id == diary.id)
            .first()
        )

        if existing_analysis:
            existing_analysis.emotion = main_emotion
            existing_analysis.score = main_score
            existing_analysis.feedback = analysis_comment
        else:
            new_analysis = models.Analysis(
                diary_id=diary.id,
                emotion=main_emotion,
                score=main_score,
                feedback=analysis_comment,
            )
            db.add(new_analysis)

        db.commit()

    except Exception as e:
        db.rollback()

        # 분석 실패 상태 기록
        try:
            diary = (
                db.query(models.Diary)
                .filter(models.Diary.id == diary_id)
                .first()
            )

            if diary and diary.analysis_version == analysis_version:
                diary.analysis_status = "failed"
                diary.analysis_completed_at = datetime.now(timezone.utc)
                db.commit()

        except Exception:
            db.rollback()

        print(f"[Emotion Analysis Error] diary_id={diary_id}: {e}")

    finally:
        db.close()


# =========================================================
# 루틴 상태 업데이트
# =========================================================

@router.post("/routine")
def update_routine_status(
    data: RoutineRequest,
    db: Session = Depends(get_db),
):
    try:
        target_date = datetime.now().date()

        routine_category = "행동"

        master_routine = (
            db.query(models.RoutineMaster)
            .filter(models.RoutineMaster.content == data.routine_name)
            .first()
        )

        if master_routine:
            routine_category = master_routine.category

        existing_diary = (
            db.query(models.Diary)
            .filter(
                models.Diary.user_id == data.user_id,
                func.date(models.Diary.created_at) == target_date,
            )
            .first()
        )

        score_diff_val = 10.0 if data.is_done else 0.0

        if existing_diary:
            existing_diary.routine_name = data.routine_name
            existing_diary.routine_category = routine_category
            existing_diary.is_done = data.is_done
            existing_diary.score_diff = score_diff_val

        else:
            new_diary = models.Diary(
                user_id=data.user_id,
                content="",
                routine_name=data.routine_name,
                routine_category=routine_category,
                is_done=data.is_done,
                score_diff=score_diff_val,
                created_at=datetime.combine(
                    target_date,
                    datetime.now().time(),
                ),
            )

            db.add(new_diary)

        user_routine = (
            db.query(models.UserRoutine)
            .join(models.RoutineMaster)
            .filter(
                models.UserRoutine.user_id == data.user_id,
                models.UserRoutine.date == target_date,
                models.RoutineMaster.content == data.routine_name,
            )
            .first()
        )

        if user_routine:
            user_routine.is_completed = data.is_done

        db.commit()

        return {
            "status": "success"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# 일기 생성 / 수정
# =========================================================

@router.post("", status_code=202)
def create_or_update_diary(
    data: DiaryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        # -------------------------------------------------
        # 1. 날짜 처리
        # -------------------------------------------------

        if data.date:
            target_date = datetime.strptime(
                data.date,
                "%Y-%m-%d",
            ).date()
        else:
            target_date = datetime.now().date()

        # -------------------------------------------------
        # 2. 일기 내용 처리
        # -------------------------------------------------

        actual_main_text = data.main_text
        packaged_content = ""

        # 구버전 프론트와 호환
        if data.content and not data.main_text:
            try:
                parsed_content = json.loads(data.content)

                actual_main_text = parsed_content.get(
                    "mainText",
                    "",
                )

                packaged_content = data.content

            except json.JSONDecodeError:
                actual_main_text = data.content
                packaged_content = data.content

        else:
            packaged_content = json.dumps(
                {
                    "mainText": data.main_text,
                    "bgColorId": data.bg_color_id,
                    "font": data.font,
                    "elements": data.elements,
                },
                ensure_ascii=False,
            )

        # -------------------------------------------------
        # 3. 같은 날짜 기존 일기 확인
        # -------------------------------------------------

        existing_diary = (
            db.query(models.Diary)
            .filter(
                models.Diary.user_id == data.user_id,
                func.date(models.Diary.created_at) == target_date,
            )
            .first()
        )

        # -------------------------------------------------
        # 4. 기존 루틴 정보 확인
        # -------------------------------------------------

        completed_routine = (
            db.query(models.UserRoutine)
            .filter(
                models.UserRoutine.user_id == data.user_id,
                models.UserRoutine.date == target_date,
                models.UserRoutine.is_completed == True,
            )
            .first()
        )

        default_routine_name = (
            completed_routine.routine_detail.content
            if (
                completed_routine
                and completed_routine.routine_detail
            )
            else None
        )

        default_routine_category = (
            completed_routine.routine_detail.category
            if (
                completed_routine
                and completed_routine.routine_detail
            )
            else None
        )

        default_is_done = (
            True if completed_routine else False
        )

        default_score_diff = (
            10.0 if completed_routine else 0.0
        )

        routine_name = (
            data.routine_name
            or default_routine_name
        )

        routine_category = (
            data.routine_category
            or default_routine_category
        )

        is_done = (
            data.is_done
            or default_is_done
        )

        score_diff = (
            data.score_diff
            if data.score_diff > 0
            else default_score_diff
        )

        # -------------------------------------------------
        # 5. DB 저장
        #
        # 여기서는 AI 분석을 하지 않는다.
        # 일기를 먼저 저장하고 processing 상태로 만든다.
        # -------------------------------------------------

        if existing_diary:
            diary = existing_diary

            diary.content = packaged_content

            # Self-Report
            if data.emotion is not None:
                diary.emotion = data.emotion

            if data.emotion_intensity is not None:
                diary.emotion_intensity = data.emotion_intensity

            diary.secondary_emotion = data.secondary_emotion
            diary.secondary_emotion_intensity = (
                data.secondary_emotion_intensity
            )

            # 루틴
            diary.routine_name = routine_name
            diary.routine_category = routine_category
            diary.score_diff = score_diff
            diary.is_done = is_done

            # 새로운 분석 시작
            diary.analysis_status = "processing"
            diary.confidence = None
            diary.bws_used = False
            diary.analysis_completed_at = None

            # 수정할 때마다 버전 증가
            diary.analysis_version = (
                diary.analysis_version or 0
            ) + 1

        else:
            diary = models.Diary(
                user_id=data.user_id,
                content=packaged_content,

                # Self-Report
                emotion=data.emotion,
                emotion_intensity=data.emotion_intensity,
                secondary_emotion=data.secondary_emotion,
                secondary_emotion_intensity=(
                    data.secondary_emotion_intensity
                ),

                # 루틴
                routine_name=routine_name,
                routine_category=routine_category,
                score_diff=score_diff,
                is_done=is_done,

                # AI 분석 상태
                analysis_status="processing",
                confidence=None,
                bws_used=False,
                analysis_completed_at=None,
                analysis_version=1,

                created_at=datetime.combine(
                    target_date,
                    datetime.now().time(),
                ),
            )

            db.add(diary)

        # diary.id 확보
        db.flush()

        diary_id = diary.id
        current_version = diary.analysis_version

        # 먼저 DB 저장
        db.commit()
        db.refresh(diary)

        # -------------------------------------------------
        # 6. 백그라운드 AI 분석 등록
        #
        # 사용자 응답을 기다리게 하지 않고,
        # FastAPI가 응답한 뒤 실행한다.
        # -------------------------------------------------

        background_tasks.add_task(
            run_emotion_analysis,
            diary_id,
            current_version,
            actual_main_text,
        )

        # -------------------------------------------------
        # 7. 즉시 응답
        # -------------------------------------------------

        return {
            "status": "processing",
            "diary_id": diary_id,
            "analysis_version": current_version,
            "message": "감정 분석을 시작했습니다.",
            "alert": None,
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# 감정 분석 상태 조회
# =========================================================

@router.get("/{diary_id}/analysis-status")
def get_analysis_status(
    diary_id: int,
    db: Session = Depends(get_db),
):
    diary = (
        db.query(models.Diary)
        .filter(models.Diary.id == diary_id)
        .first()
    )

    if not diary:
        raise HTTPException(
            status_code=404,
            detail="일기를 찾을 수 없습니다.",
        )

    response = {
        "diary_id": diary.id,
        "status": diary.analysis_status,
        "confidence": diary.confidence,
        "bws_used": diary.bws_used,
        "analysis_completed_at": diary.analysis_completed_at,
        "analysis_version": diary.analysis_version,
    }

    # 완료됐을 때만 최종 8감정 전달
    if diary.analysis_status == "completed":
        response["emotions"] = {
            key: getattr(diary, key, 0.0)
            for key in EMOTION_KEYS
        }

    return response


# =========================================================
# 월별 일기 조회
# =========================================================

@router.get("/monthly")
def get_monthly_diaries(
    user_id: str,
    year: int = Query(..., example=2026),
    month: int = Query(..., example=5),
    db: Session = Depends(get_db),
):
    diaries = (
        db.query(models.Diary)
        .filter(
            models.Diary.user_id == user_id,
            extract(
                "year",
                models.Diary.created_at,
            ) == year,
            extract(
                "month",
                models.Diary.created_at,
            ) == month,
        )
        .order_by(
            models.Diary.created_at.asc()
        )
        .all()
    )

    return {
        "data": [
            {
                "date": d.created_at.strftime(
                    "%Y-%m-%d"
                ),

                # Self-Report
                "emotion": d.emotion,
                "emotion_intensity": d.emotion_intensity,
                "secondary_emotion": d.secondary_emotion,
                "secondary_emotion_intensity": d.secondary_emotion_intensity,

                # 일기 내용
                "content": d.content,

                # AI 분석 상태
                "analysis_status": d.analysis_status,
            }
            for d in diaries
        ]
    }

# =========================================================
# 일기 삭제
# =========================================================

@router.delete("")
def delete_diary(
    user_id: str,
    date: str,
    db: Session = Depends(get_db),
):
    try:
        target_date = datetime.strptime(
            date,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="날짜 형식이 올바르지 않습니다.",
        )

    diary_to_delete = (
        db.query(models.Diary)
        .filter(
            models.Diary.user_id == user_id,
            func.date(
                models.Diary.created_at
            ) == target_date,
        )
        .first()
    )

    if not diary_to_delete:
        raise HTTPException(
            status_code=404,
            detail="해당 날짜의 일기가 없습니다.",
        )

    # 기존 Analysis 데이터가 있으면 같이 삭제
    analysis_rows = (
        db.query(models.Analysis)
        .filter(
            models.Analysis.diary_id
            == diary_to_delete.id
        )
        .all()
    )

    for row in analysis_rows:
        db.delete(row)

    db.delete(diary_to_delete)
    db.commit()

    return {
        "status": "success"
    }