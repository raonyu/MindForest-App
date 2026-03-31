from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from sqlalchemy.orm import Session
import models
from pydantic import BaseModel
from typing import List

router = APIRouter()

# --- 1. 요청 데이터 모델 ---
class AnswerItem(BaseModel):
    question_num: int  # 1~9번 문항 번호
    answer: int        # 선택한 점수

class SurveyRequest(BaseModel):
    user_id: str
    survey_type: str   # "PHQ-9", "K-MDQ", "ASRS" 등
    answers: List[AnswerItem]

# --- 2. [GET] 특정 질환의 전문 설문 문항 가져오기 ---
@router.get("/api/survey/{survey_type}")
def get_survey_questions(survey_type: str, db: Session = Depends(get_db)):
    """
    GPT가 배정한 질환 타입에 맞는 9개 전문 문항을 DB에서 가져옵니다.
    """
    questions = db.query(models.Survey).filter(
        models.Survey.survey_type == survey_type.upper()
    ).order_by(models.Survey.question_num.asc()).all()

    if not questions:
        raise HTTPException(status_code=404, detail="해당 설문지를 찾을 수 없습니다.")

    return questions

# --- 3. [POST] 설문 답변 제출 및 결과 분석 저장 ---
@router.post("/api/survey/submit")
def submit_survey(data: SurveyRequest, db: Session = Depends(get_db)):
    """
    사용자의 정밀 설문 답변을 받아 각 질환별 로직에 따라 채점하고 결과를 저장합니다.
    """
    try:
        answers_dict = {a.question_num: a.answer for a in data.answers}
        total_score = 0
        result_message = ""

        # --- [질환별 채점 로직 분기] ---
        stype = data.survey_type.upper()

        # 1. 단순 합산형 (PHQ-9, GAD-7, PCL-5, Y-BOCS, DAR-5)
        if stype in ["PHQ-9", "GAD-7", "PCL-5", "Y-BOCS", "DAR-5"]:
            total_score = sum(answers_dict.values())
            
            # 예시: PHQ-9 기준 판정 (다른 질환은 기준점에 따라 세분화 필요)
            if stype == "PHQ-9":
                if total_score <= 4: result_message = "우울 아님"
                elif total_score <= 9: result_message = "가벼운 우울"
                elif total_score <= 14: result_message = "중간 정도 우울"
                else: result_message = "심한 우울"
            else:
                result_message = f"{stype} 분석 완료 (총점: {total_score})"

        # 2. 조울증 (K-MDQ) - 조건부 로직
        elif stype == "K-MDQ":
            # 1단계 13문항 중 '예(1)'가 7개 이상인지 확인 등
            yes_count = sum(1 for q, a in answers_dict.items() if q <= 13 and a == 1)
            if yes_count >= 7 and answers_dict.get(14) == 1:
                result_message = "조울증 가능성 높음"
            else:
                result_message = "조울증 가능성 낮음"
            total_score = yes_count

        # 3. ADHD (ASRS) - 특정 구역 체크 로직
        elif stype == "ASRS":
            # 1~3번은 2점 이상(가끔~), 4~6번은 3점 이상(자주~)일 때 카운트
            critical_points = 0
            for q in range(1, 4):
                if answers_dict.get(q, 0) >= 2: critical_points += 1
            for q in range(4, 7):
                if answers_dict.get(q, 0) >= 3: critical_points += 1
            
            if critical_points >= 4: result_message = "ADHD 가능성 높음 (추가 진단 권유)"
            else: result_message = "정상 범위"
            total_score = critical_points

        # --- [결과 저장 절차] ---
        
        # 1. 개별 답변 상세 저장
        for q_num, ans in answers_dict.items():
            new_answer = models.SurveyAnswer(
                user_id=data.user_id,
                survey_type=stype,
                question_num=q_num,
                answer=ans
            )
            db.add(new_answer)

        # 2. 최종 합계 결과 저장
        new_result = models.SurveyResult(
            user_id=data.user_id,
            survey_type=stype,
            score=total_score,
            result_message=result_message
        )
        db.add(new_result)
        
        db.commit()
        return {"survey_type": stype, "score": total_score, "result": result_message}

    except Exception as e:
        db.rollback()
        print(f"Error in survey submit: {str(e)}")
        raise HTTPException(status_code=500, detail="설문 저장 중 오류가 발생했습니다.")