from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from sqlalchemy.orm import Session
import models
from pydantic import BaseModel
from typing import List

router = APIRouter()

class AnswerItem(BaseModel):
    question_num: int
    answer: int

class SurveyRequest(BaseModel):
    user_id: str
    survey_type: str 
    answers: List[AnswerItem]

class SurveyQuestionResponse(BaseModel):
    id: int
    survey_type: str
    question_num: int
    question_text: str

    class Config:
        from_attributes = True

@router.get("/{survey_type}", response_model=List[SurveyQuestionResponse])
def get_survey_questions(survey_type: str, db: Session = Depends(get_db)):
    questions = db.query(models.Survey).filter(
        models.Survey.survey_type == survey_type.upper()
    ).order_by(models.Survey.question_num.asc()).all()

    if not questions:
        raise HTTPException(status_code=404, detail="해당 설문지를 찾을 수 없습니다.")
    return questions

@router.post("/submit")
def submit_survey(data: SurveyRequest, db: Session = Depends(get_db)):
    try:
        # [디버깅] 실제로 몇 개의 답변이 들어오는지 터미널에 출력합니다.
        print(f"DEBUG: 받은 답변 개수 = {len(data.answers)}")
        
        # 모든 answer 값을 직접 합산 (중복 question_num이 있어도 모두 더함)
        total_score = sum(a.answer for a in data.answers)
        print(f"DEBUG: 합산된 총점 = {total_score}")
        
        result_message = ""
        stype = data.survey_type.upper()
        is_normal = False

        # 질환별 판정 로직
        if stype == "DEPRESSION":
            if total_score <= 4: result_message = "현재 정상 범위 내에 있습니다."; is_normal = True
            elif total_score <= 9: result_message = "가벼운 우울감이 느껴지는 단계입니다."
            elif total_score <= 14: result_message = "중간 정도의 우울감이 있으니 주의가 필요합니다."
            else: result_message = "심한 우울 증세가 의심됩니다."
        
        elif stype == "ANXIETY":
            if total_score <= 4: result_message = "불안 수준이 낮고 안정적입니다."; is_normal = True
            elif total_score <= 9: result_message = "경미한 불안 상태입니다."
            elif total_score <= 14: result_message = "중간 정도의 불안감이 느껴지는 단계입니다."
            else: result_message = "심한 불안 증세가 의심됩니다."
        
        elif stype == "ADHD":
            # ADHD는 3점 이상(자주)인 문항의 개수가 점수가 됩니다.
            critical_points = sum(1 for a in data.answers if a.answer >= 3)
            total_score = critical_points
            if critical_points >= 4: result_message = "성인 ADHD 경향성이 뚜렷합니다."
            else: result_message = "정상 범위입니다."; is_normal = True
        
        else:
            if total_score <= 10: result_message = "정상 범위 내에 있습니다."; is_normal = True
            else: result_message = "관리가 필요한 상태입니다."

        # DB 저장: 기존 결과가 있다면 덮어쓰지 않고 새로 추가 (이력 관리)
        for a in data.answers:
            db.add(models.SurveyAnswer(
                user_id=data.user_id, 
                survey_type=stype, 
                question_num=a.question_num, 
                answer=a.answer
            ))
        
        db.add(models.SurveyResult(
            user_id=data.user_id, 
            survey_type=stype, 
            score=total_score, 
            result_message=result_message
        ))
        
        db.commit()
        return {"status": "success", "score": total_score, "result": result_message, "is_normal": is_normal}

    except Exception as e:
        db.rollback()
        print(f"ERROR: 설문 제출 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))