from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from datetime import datetime, timezone
from pydantic import BaseModel
from services.ai_logic import analyze_diary_emotion, check_anomaly_level

# --- 1. 요청 데이터 모델 ---
class DiaryRequest(BaseModel):
    user_id: str
    content: str
    routine_name: str = None  # 예: "5분 광합성", "명상하기"
    is_done: bool = False     # 루틴 완료 여부

router = APIRouter()

@router.post("/api/diary")
def create_diary(data: DiaryRequest, db: Session = Depends(get_db)):
    try:
        # --- [STEP 1] AI 감정 분석 호출 ---
        # gpt-4o-mini를 통해 8가지 감정 수치와 요약 코멘트를 가져옵니다.
        analysis = analyze_diary_emotion(data.content)
        if not analysis:
            raise HTTPException(status_code=500, detail="AI 분석에 실패했습니다.")

        emotions = analysis["emotions"]
        comment = analysis["analysis_comment"]

        # --- [STEP 2] Diary 테이블 저장 (루틴 데이터 포함) ---
        new_diary = models.Diary(
            user_id=data.user_id,
            content=data.content,
            routine_name=data.routine_name, # 조원 C의 루틴 랭킹 로직용
            is_done=data.is_done,           # 조원 C의 루틴 랭킹 로직용
            analysis_comment=comment,
            **emotions # 8가지 감정 필드에 자동 매핑 (joy, sadness 등)
        )
        db.add(new_diary)
        # flush를 사용해 ID를 먼저 생성합니다 (Analysis 테이블 외래키 연결용)
        db.flush() 

        # --- [STEP 3] Analysis 테이블 저장 (조원 C의 '마음의 가면' 로직용) ---
        # 가장 높은 점수를 가진 감정을 추출하여 대표 감정으로 기록합니다.
        main_emotion = max(emotions, key=emotions.get) if emotions else "unknown"
        ai_score = emotions.get(main_emotion, 0.0)

        new_analysis = models.Analysis(
            diary_id=new_diary.id,
            emotion=main_emotion, # 예: "sadness"
            score=ai_score,       # 예: 85.0
            feedback=comment      # AI의 요약 코멘트를 피드백으로 활용
        )
        db.add(new_analysis)

        # --- [STEP 4] 이상징후 탐지를 위한 과거 데이터 조회 (최근 7일치) ---
        # 1. 최신순(desc)으로 7개를 먼저 가져와야 방금 쓴 일기가 포함됩니다.
        subquery = db.query(models.Diary)\
            .filter(models.Diary.user_id == data.user_id)\
            .order_by(models.Diary.created_at.desc())\
            .limit(7)\
            .all()

        # 2. 시간대(naive vs aware) 충돌을 방지하며 다시 시간순(asc)으로 정렬합니다.
        recent_diaries = sorted(
            subquery, 
            key=lambda x: x.created_at.replace(tzinfo=timezone.utc) if x.created_at.tzinfo is None else x.created_at
        )

        # [디버깅] 데이터 개수 확인
        print(f"DEBUG: 유저 {data.user_id}의 분석 대상 데이터 수 = {len(recent_diaries)}")

        # 3. AI 로직(check_anomaly_level)에 보낼 감정 리스트 가공
        emotion_list = [
            {
                "emotions": {
                    "sadness": d.sadness or 0, 
                    "anger": d.anger or 0,
                    "fear": d.fear or 0,
                    "disgust": d.disgust or 0,
                    "joy": d.joy or 0
                }
            }
            for d in recent_diaries
        ]

        # --- [STEP 5] 이상징후 검사 실행 ---
        # 최근 7일간의 감정 흐름을 분석하여 LOW/MEDIUM/HIGH 단계를 결정합니다.
        alert = check_anomaly_level(emotion_list)

        # 모든 작업이 성공하면 한꺼번에 커밋합니다 (원자성 보장)
        db.commit() 
        db.refresh(new_diary)

        # --- [STEP 6] 결과 반환 ---
        return {
            "message": "일기 및 루틴 저장, AI 분석 완료",
            "diary_id": new_diary.id,
            "analysis": analysis, # GPT의 전체 분석 데이터
            "alert": alert        # 이상징후 경고 단계
        }
        
    except Exception as e:
        # 중간에 에러가 나면 DB를 깨끗하게 롤백합니다.
        db.rollback() 
        print(f"ERROR in create_diary: {str(e)}") # 서버 로그용
        raise HTTPException(status_code=500, detail="일기 저장 중 서버 오류가 발생했습니다.")