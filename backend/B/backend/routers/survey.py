from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal, get_db
from sqlalchemy.orm import Session
import models
from pydantic import BaseModel
from typing import List


router = APIRouter()


class AnswerItem(BaseModel):
    question_id: int
    answer: int


class SurveyRequest(BaseModel):
    user_id: str
    answers: List[AnswerItem]


@router.get("/api/survey/phq9")
def get_phq9():

    db = SessionLocal()

    try:
        questions = db.query(models.Survey).filter(
            models.Survey.survey_type == "phq9"
        ).all()

        return questions

    finally:
        db.close()


@router.post("/api/survey/phq9")
def submit_phq9(data: SurveyRequest, db: Session = Depends(get_db)):
    try:
        total_score = sum(a.answer for a in data.answers)

        # 1. 개별 답변 저장
        for a in data.answers:
            new_answer = models.SurveyAnswer(
                user_id=data.user_id,
                survey_type="phq9",
                question_id=a.question_id,
                answer=a.answer
            )
            db.add(new_answer)

        # 2. 결과 판정 (세분화 가능)
        if total_score <= 4: result = "우울 아님"
        elif total_score <= 9: result = "가벼운 우울"
        elif total_score <= 14: result = "중간 정도 우울"
        elif total_score <= 19: result = "중간 정도 심한 우울"
        else: result = "심한 우울"

        # 3. 최종 결과 저장
        new_result = models.SurveyResult(
            user_id=data.user_id,
            survey_type="phq9",
            score=total_score,
            result=result
        )
        db.add(new_result)
        
        db.commit() # 모든 과정이 성공했을 때만 DB에 반영
        return {"score": total_score, "result": result}

    except Exception as e:
        db.rollback() # 에러 발생 시 진행 중인 저장 취소
        raise HTTPException(status_code=500, detail="설문 저장 중 오류 발생")