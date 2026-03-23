from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from pydantic import BaseModel
from services.ai_logic import analyze_diary_emotion, check_anomaly_level

# 1. 프론트엔드에서 루틴 데이터를 함께 받을 수 있게 모델 확장
class DiaryRequest(BaseModel):
    user_id: str
    content: str
    routine_name: str = None  # 추가: "5분 광합성" 등
    is_done: bool = False     # 추가: 했는지 안 했는지 여부

router = APIRouter()

@router.post("/api/diary")
def create_diary(data: DiaryRequest, db: Session = Depends(get_db)):
    try:
        # 1. AI 감정 분석 호출
        analysis = analyze_diary_emotion(data.content)
        if not analysis:
            raise HTTPException(status_code=500, detail="AI 분석에 실패했습니다.")

        emotions = analysis["emotions"]
        comment = analysis["analysis_comment"]

        # 2. Diary 테이블 저장 (루틴 데이터 포함)
        new_diary = models.Diary(
            user_id=data.user_id,
            content=data.content,
            routine_name=data.routine_name, # C의 5번 로직용
            is_done=data.is_done,           # C의 5번 로직용
            analysis_comment=comment,
            **emotions 
        )
        db.add(new_diary)
        db.flush() # ID를 먼저 생성해서 Analysis 테이블 연동에 쓰기 위함

        # 3. Analysis 테이블 저장 (C의 10번 '마음의 가면' 로직용)
        # GPT가 분석한 주된 감정명과 강도 점수(score)를 별도로 기록합니다.
        
        main_emotion = max(emotions, key=emotions.get) if emotions else "unknown"
        
        ai_score = emotions.get(main_emotion, 0.0)

        new_analysis = models.Analysis(
            diary_id=new_diary.id,
            emotion=main_emotion,
            score=ai_score, # C가 요청한 'GPT 점수'
            feedback=comment
        )
        db.add(new_analysis)

        # 4. 이상징후 탐지를 위한 과거 데이터 조회 (최근 7일치)
        recent_diaries = db.query(models.Diary)\
            .filter(models.Diary.user_id == data.user_id)\
            .order_by(models.Diary.created_at.asc())\
            .limit(7)\
            .all()

        emotion_list = [
            {"emotions": {"sadness": d.sadness or 0, "anger": d.anger or 0}}
            for d in recent_diaries
        ]

        # 5. 이상징후 검사
        alert = check_anomaly_level(emotion_list)

        db.commit() # 모든 저장이 완료되면 커밋
        db.refresh(new_diary)

        return {
            "message": "일기 및 루틴 저장, AI 분석 완료",
            "diary_id": new_diary.id,
            "analysis": analysis,
            "alert": alert
        }
        
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=str(e))