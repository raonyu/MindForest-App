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

@router.get("/api/survey/{survey_type}")
def get_survey_questions(survey_type: str, db: Session = Depends(get_db)):
    questions = db.query(models.Survey).filter(
        models.Survey.survey_type == survey_type.upper()
    ).order_by(models.Survey.question_num.asc()).all()

    if not questions:
        raise HTTPException(status_code=404, detail="해당 설문지를 찾을 수 없습니다.")
    return questions

@router.post("/api/survey/submit")
def submit_survey(data: SurveyRequest, db: Session = Depends(get_db)):
    try:
        answers_dict = {a.question_num: a.answer for a in data.answers}
        total_score = 0
        result_message = ""
        stype = data.survey_type.upper()

        # [1] 단순 합산형 질환 (7종)
        # 모든 문항의 점수를 그냥 더하는 방식입니다.
        simple_sum_types = [
            "DEPRESSION", "ANXIETY", "PTSD", "OCD", 
            "ANGER", "EATING_DISORDER", "SCHIZOPHRENIA"
        ]
        
        if stype in simple_sum_types:
            total_score = sum(answers_dict.values())
            
            # 질환별 상세 판정 기준 (예시: DEPRESSION)
            if stype == "DEPRESSION":
                if total_score <= 4: result_message = "정상 범위입니다."
                elif total_score <= 9: result_message = "가벼운 우울감이 느껴집니다."
                elif total_score <= 14: result_message = "중간 정도의 우울감이 있습니다."
                else: result_message = "심한 우울 증세가 의심됩니다. 전문가의 상담을 권장합니다."
            else:
                # 나머지 6종은 일단 총점 안내로 공통 처리
                result_message = f"{stype} 분석 결과, 총점 {total_score}점이 나왔습니다."

        # [2] 조울증 (BIPOLAR) - 특별 로직
        elif stype == "BIPOLAR":
            # 9문항 중 2점 이상(예)인 항목의 개수를 셉니다.
            yes_count = sum(1 for a in answers_dict.values() if a >= 2)
            total_score = yes_count
            if yes_count >= 7:
                result_message = "조울증(양극성 장애) 가능성이 높습니다."
            else:
                result_message = "조울증 가능성이 낮습니다."

        # [3] ADHD (ADHD) - 특별 로직
        elif stype == "ADHD":
            # 특정 문항에서 '자주(3점 이상)' 체크된 항목을 셉니다.
            critical_points = sum(1 for a in answers_dict.values() if a >= 3)
            total_score = critical_points
            if critical_points >= 4:
                result_message = "ADHD 성향이 강하게 나타납니다. 정밀 검사를 권장합니다."
            else:
                result_message = "정상 범위입니다."

        else:
            raise HTTPException(status_code=400, detail="잘못된 설문 유형입니다.")

        # --- [DB 저장 로직] ---
        # 개별 답변 저장
        for q_num, ans in answers_dict.items():
            db.add(models.SurveyAnswer(
                user_id=data.user_id, survey_type=stype,
                question_num=q_num, answer=ans
            ))

        # 최종 결과 저장
        db.add(models.SurveyResult(
            user_id=data.user_id, survey_type=stype,
            score=total_score, result_message=result_message
        ))
        
        db.commit()
        return {"survey_type": stype, "score": total_score, "result": result_message}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"저장 중 에러: {str(e)}")