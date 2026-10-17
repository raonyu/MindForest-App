import json
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

import models
import routine_manager
from database import get_db
from services.ai_logic import check_anomaly_level
from services.emotion_pipeline import analyze_emotion_pipeline


# --- [1. 요청 데이터 모델] ---
class DiaryRequest(BaseModel):
    user_id: str
    date: Optional[str] = None
    emotion: Optional[str] = None

    # 다꾸용 분리 데이터 컬럼들
    main_text: str = ""
    bg_color_id: str = "#ffffff"
    font: str = "System"
    elements: List[Any] = []

    routine_name: Optional[str] = None
    routine_category: Optional[str] = None
    score_diff: float = 0.0
    is_done: bool = False
    content: Optional[str] = None  # 구버전 호환용 방어코드


class RoutineRequest(BaseModel):
    user_id: str
    routine_name: str
    is_done: bool


router = APIRouter()


# --- [2. 루틴 상태 업데이트 (POST)] ---
@router.post("/routine")
def update_routine_status(data: RoutineRequest, db: Session = Depends(get_db)):
    try:
        target_date = datetime.now().date()

        routine_category = "활동형"
        master_routine = db.query(models.RoutineMaster).filter(
            models.RoutineMaster.content == data.routine_name
        ).first()
        if master_routine:
            routine_category = master_routine.category

        existing_diary = db.query(models.Diary).filter(
            models.Diary.user_id == data.user_id,
            func.date(models.Diary.created_at) == target_date
        ).first()

        score_diff_val = 0.0

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
                created_at=datetime.combine(target_date, datetime.now().time())
            )
            db.add(new_diary)

        user_routine = db.query(models.UserRoutine).join(models.RoutineMaster).filter(
            models.UserRoutine.user_id == data.user_id,
            models.UserRoutine.date == target_date,
            models.RoutineMaster.content == data.routine_name
        ).first()
        if user_routine:
            user_routine.is_completed = data.is_done

        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# --- [3. 일기 저장 및 수정 (POST)] ---
@router.post("")
def create_or_update_diary(data: DiaryRequest, db: Session = Depends(get_db)):
    try:
        # 1. 날짜 및 텍스트 처리
        if data.date:
            target_date = datetime.strptime(data.date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()

        actual_main_text = data.main_text
        packaged_content = ""

        if data.content and not data.main_text:
            try:
                parsed_content = json.loads(data.content)
                actual_main_text = parsed_content.get("mainText", "")
                packaged_content = data.content
            except json.JSONDecodeError:
                actual_main_text = data.content
                packaged_content = data.content
        else:
            packaged_content = json.dumps({
                "mainText": data.main_text,
                "bgColorId": data.bg_color_id,
                "font": data.font,
                "elements": data.elements
            }, ensure_ascii=False)

        # 2. AI 감정 분석 (1차 KoELECTRA + 2차 BWS 검증)
        analysis = analyze_emotion_pipeline(actual_main_text)
        if not analysis:
            raise HTTPException(status_code=500, detail="AI 분석 실패")

        emotions = analysis.get("emotions", {})
        analysis_comment = analysis.get("analysis_comment", "")
        
        # 프론트에서 지정한 감정이 없으면 BWS 승리 감정(또는 1차 최고점 감정)을 대표 감정으로 설정
        main_emotion = (
            data.emotion
            or analysis.get("dominant_emotion")
            or (max(emotions, key=emotions.get) if emotions else "joy")
        )

        # 3. 루틴 자동 동기화 조회
        completed_routine = db.query(models.UserRoutine).filter(
            models.UserRoutine.user_id == data.user_id,
            models.UserRoutine.date == target_date,
            models.UserRoutine.is_completed == True
        ).first()

        default_routine_name = completed_routine.routine_detail.content if (completed_routine and completed_routine.routine_detail) else None
        default_routine_category = completed_routine.routine_detail.category if (completed_routine and completed_routine.routine_detail) else None
        default_is_done = True if completed_routine else False

        routine_name = data.routine_name or default_routine_name
        routine_category = data.routine_category or default_routine_category
        is_done = data.is_done or default_is_done
        score_diff = 0.0

        # 4. Diary 테이블 Upsert (저장 또는 덮어쓰기)
        existing_diary = db.query(models.Diary).filter(
            models.Diary.user_id == data.user_id,
            func.date(models.Diary.created_at) == target_date
        ).first()

        record_time = datetime.combine(target_date, datetime.now().time())

        if existing_diary:
            existing_diary.content = packaged_content
            existing_diary.emotion = main_emotion
            existing_diary.routine_name = routine_name
            existing_diary.routine_category = routine_category
            existing_diary.score_diff = score_diff
            existing_diary.is_done = is_done
            existing_diary.analysis_comment = analysis_comment

            for k, v in emotions.items():
                setattr(existing_diary, k, v)
            new_diary = existing_diary
        else:
            new_diary = models.Diary(
                user_id=data.user_id,
                content=packaged_content,
                emotion=main_emotion,
                routine_name=routine_name,
                routine_category=routine_category,
                score_diff=score_diff,
                is_done=is_done,
                analysis_comment=analysis_comment,
                created_at=record_time,
                **emotions
            )
            db.add(new_diary)

        db.flush()

        # 5. Analysis 테이블 Upsert (중복 생성 방지)
        existing_analysis = db.query(models.Analysis).filter(
            models.Analysis.diary_id == new_diary.id
        ).first()

        if existing_analysis:
            existing_analysis.emotion = main_emotion
            existing_analysis.score = emotions.get(main_emotion, 0.0)
            existing_analysis.feedback = analysis_comment
        else:
            new_analysis = models.Analysis(
                diary_id=new_diary.id,
                emotion=main_emotion,
                score=emotions.get(main_emotion, 0.0),
                feedback=analysis_comment
            )
            db.add(new_analysis)

        # 6. BwsRecord 테이블 저장 (주간 리포트 '복합 감정 데이' 카드 연동)
        if hasattr(models, "BwsRecord"):
            # 같은 날짜의 기존 BWS 기록이 있으면 정리 후 재삽입
            db.query(models.BwsRecord).filter(
                models.BwsRecord.user_id == data.user_id,
                func.date(models.BwsRecord.created_at) == target_date
            ).delete(synchronize_session=False)

            if analysis.get("bws_used") and analysis.get("bws_validation"):
                bws_val = analysis["bws_validation"]
                candidates_list = bws_val.get("candidates", [])
                candidates_str = ",".join(candidates_list) if isinstance(candidates_list, list) else str(candidates_list)

                bws_kwargs: dict[str, Any] = {
                    "user_id": data.user_id,
                    "candidates": candidates_str,
                    "best_emotion": bws_val.get("best_emotion"),
                    "worst_emotion": bws_val.get("worst_emotion"),
                    "reasoning": bws_val.get("reasoning", ""),
                    "created_at": record_time,
                }
                if hasattr(models.BwsRecord, "diary_id"):
                    bws_kwargs["diary_id"] = new_diary.id

                # models.BwsRecord에 정의된 컬럼만 안전하게 매핑
                valid_bws_kwargs = {
                    k: v for k, v in bws_kwargs.items() if hasattr(models.BwsRecord, k)
                }
                db.add(models.BwsRecord(**valid_bws_kwargs))

        # 7. 최근 7일 이상징후 체크
        recent_diaries = (
            db.query(models.Diary)
            .filter(models.Diary.user_id == data.user_id)
            .order_by(models.Diary.created_at.desc())
            .limit(7)
            .all()
        )

        emotion_list = [{"emotions": {k: getattr(d, k, 0.0) for k in emotions.keys()}} for d in recent_diaries]
        alert = check_anomaly_level(emotion_list)

        db.commit()
        db.refresh(new_diary)

        return {
            "status": "success",
            "diary_id": new_diary.id,
            "dominant_emotion": main_emotion,
            "bws_used": analysis.get("bws_used", False),
            "alert": alert
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# --- [4. 월별 일기 불러오기 (GET)] ---
@router.get("/monthly")
def get_monthly_diaries(
    user_id: str,
    year: int = Query(..., example=2026),
    month: int = Query(..., example=5),
    db: Session = Depends(get_db)
):
    diaries = db.query(models.Diary).filter(
        models.Diary.user_id == user_id,
        extract('year', models.Diary.created_at) == year,
        extract('month', models.Diary.created_at) == month
    ).order_by(models.Diary.created_at.asc()).all()

    return {
        "data": [
            {
                "date": d.created_at.strftime("%Y-%m-%d"),
                "emotion": d.emotion or "joy",
                "content": d.content
            } for d in diaries
        ]
    }


# --- [5. 특정 일기 삭제 (DELETE)] ---
@router.delete("")
def delete_diary(user_id: str, date: str, db: Session = Depends(get_db)):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다.")

    diary_to_delete = db.query(models.Diary).filter(
        models.Diary.user_id == user_id,
        func.date(models.Diary.created_at) == target_date
    ).first()

    if not diary_to_delete:
        raise HTTPException(status_code=404, detail="해당 날짜의 일기가 없습니다.")

    db.delete(diary_to_delete)
    db.commit()

    return {"status": "success"}