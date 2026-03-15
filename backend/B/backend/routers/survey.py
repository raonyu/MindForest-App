from fastapi import APIRouter
from database import SessionLocal
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
def submit_phq9(data: SurveyRequest):

    db = SessionLocal()

    try:
        user_id = data.user_id
        answers = data.answers

        total_score = 0

        for a in answers:

            total_score += a.answer

            new_answer = models.SurveyAnswer(
                user_id=user_id,
                survey_type="phq9",
                question_id=a.question_id,
                answer=a.answer
            )

            db.add(new_answer)

        # 점수 판정
        if total_score <= 4:
            result = "우울 아님"
        elif total_score <= 9:
            result = "가벼운 우울"
        elif total_score <= 19:
            result = "중간 정도 우울"
        else:
            result = "심한 우울"

        new_result = models.SurveyResult(
            user_id=user_id,
            survey_type="phq9",
            score=total_score,
            result=result
        )

        db.add(new_result)
        db.commit()

        return {
            "score": total_score,
            "result": result
        }

    finally:
        db.close()