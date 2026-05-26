import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from database import get_db
import models
from pydantic import BaseModel
from typing import List, Any, Optional
from services.ai_logic import analyze_diary_emotion, check_anomaly_level
from datetime import datetime
import routine_manager

# --- [1. 요청 데이터 모델] ---
# 💡 프론트엔드에서 분리해서 보내는 데이터를 받도록 바구니를 고쳤습니다.
class DiaryRequest(BaseModel):
    user_id: str
    date: str = None  
    emotion: str = None  
    
    # 다꾸용 분리 데이터 컬럼들
    main_text: str = ""
    bg_color_id: str = "#ffffff"
    font: str = "System"
    elements: List[Any] = []
    
    routine_name: Optional[str] = None
    routine_category: Optional[str] = None 
    score_diff: float = 0.0      
    is_done: bool = False
    content: Optional[str] = None  # 옛날 버전 호환용 방어코드

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
        # [수정] DB의 RoutineMaster 테이블을 조회하여 실제 등록된 카테고리를 실시간으로 획득합니다.
        master_routine = db.query(models.RoutineMaster).filter(
            models.RoutineMaster.content == data.routine_name
        ).first()
        if master_routine:
            routine_category = master_routine.category

        existing_diary = db.query(models.Diary).filter(
            models.Diary.user_id == data.user_id,
            func.date(models.Diary.created_at) == target_date
        ).first()

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
                created_at=datetime.combine(target_date, datetime.now().time())
            )
            db.add(new_diary)

        # [동기화] user_routines 테이블 상태도 동일하게 업데이트하여 완벽하게 연계되도록 함
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
# 💡 질문하신 핵심 로직이 바로 이 함수 공간에 들어간 것입니다!
@router.post("")
def create_or_update_diary(data: DiaryRequest, db: Session = Depends(get_db)):
    try:
        # 1. 날짜 처리
        if data.date:
            target_date = datetime.strptime(data.date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()

        actual_main_text = data.main_text
        packaged_content = ""

        # 구버전 프론트와 신버전 프론트 양쪽 다 동작하도록 자동 압축 포장하는 로직
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

        # 2. AI 감정 분석 (코멘트 없이 8가지 감정 스코어만 추출)
        analysis = analyze_diary_emotion(actual_main_text)
        if not analysis:
            raise HTTPException(status_code=500, detail="AI 분석 실패")

        emotions = analysis.get("emotions", {})

        # 3. 데이터베이스에 넣기 (Upsert)
        existing_diary = db.query(models.Diary).filter(
            models.Diary.user_id == data.user_id,
            func.date(models.Diary.created_at) == target_date
        ).first()

        # [자동 동기화] 오늘 완료한 루틴이 있다면 가져와서 세팅합니다.
        completed_routine = db.query(models.UserRoutine).filter(
            models.UserRoutine.user_id == data.user_id,
            models.UserRoutine.date == target_date,
            models.UserRoutine.is_completed == True
        ).first()
        
        # 클라이언트(프론트엔드)에서 루틴 전송이 누락된 경우 DB에 저장된 완료 상태를 기반으로 필드 자동 구성
        default_routine_name = completed_routine.routine_detail.content if (completed_routine and completed_routine.routine_detail) else None
        default_routine_category = completed_routine.routine_detail.category if (completed_routine and completed_routine.routine_detail) else None
        default_is_done = True if completed_routine else False
        default_score_diff = 10.0 if completed_routine else 0.0

        routine_name = data.routine_name or default_routine_name
        routine_category = data.routine_category or default_routine_category
        is_done = data.is_done or default_is_done
        score_diff = data.score_diff if data.score_diff > 0 else default_score_diff

        if existing_diary:
            # 기존 일기가 있으면 덮어쓰기 (Update)
            existing_diary.content = packaged_content
            existing_diary.emotion = data.emotion or existing_diary.emotion
            
            # 자동 동기화 데이터 및 클라이언트 전송 데이터 융합 적용
            existing_diary.routine_name = routine_name
            existing_diary.routine_category = routine_category
            existing_diary.score_diff = score_diff
            existing_diary.is_done = is_done
            
            # 8가지 감정 점수 매핑 업데이트
            for k, v in emotions.items():
                setattr(existing_diary, k, v)
            new_diary = existing_diary
        else:
            # 없으면 새로 생성 (Insert)
            new_diary = models.Diary(
                user_id=data.user_id,
                content=packaged_content,
                emotion=data.emotion,
                routine_name=routine_name,
                routine_category=routine_category,
                score_diff=score_diff,
                is_done=is_done,
                created_at=datetime.combine(target_date, datetime.now().time()),
                **emotions
            )
            db.add(new_diary)
        
        db.flush() 

        # 4. Analysis 테이블 저장 (피드백 코멘트는 빈 칸 처리)
        main_emotion = data.emotion if data.emotion else (max(emotions, key=emotions.get) if emotions else "unknown")
        new_analysis = models.Analysis(
            diary_id=new_diary.id,
            emotion=main_emotion,
            score=emotions.get(main_emotion, 0.0),
            feedback="" 
        )
        db.add(new_analysis)

        # 5. 이상징후 체크
        recent_diaries = db.query(models.Diary)\
            .filter(models.Diary.user_id == data.user_id)\
            .order_by(models.Diary.created_at.desc())\
            .limit(7)\
            .all()
        
        emotion_list = [{"emotions": {k: getattr(d, k, 0.0) for k in emotions.keys()}} for d in recent_diaries]
        alert = check_anomaly_level(emotion_list)

        db.commit()
        db.refresh(new_diary)

        return {
            "status": "success",
            "diary_id": new_diary.id,
            "alert": alert
        }
        
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
                "emotion": getattr(d, 'emotion', "joy"),
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