from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from services.chatbot_logic import get_chat_response
# [추가] C의 루틴 관리 로직 연동 (루틴 추천이나 상태 확인용)
import routine_manager
from pydantic import BaseModel
import json
from datetime import datetime

# 1. 프론트엔드로부터 받을 데이터 규격
class ChatRequest(BaseModel):
    user_id: str
    message: str

router = APIRouter()

@router.post("/api/chat")
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    # [1] 사용자 확인 및 가입일(signup_date) 확인
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # [요구사항 2] 가입일(signup_date) 정보 추출 (Pandas 분석용 timezone 적용 확인)
    # user.created_at은 models.py에서 DateTime(timezone=True)로 설정됨
    signup_date = user.created_at

    # [2] 과거 대화 내역 불러오기
    history_objs = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.user_id == data.user_id)\
        .order_by(models.ChatHistory.created_at.asc())\
        .all()
    
    chat_history = []
    for h in history_objs:
        chat_history.append({"role": h.role, "content": h.content})

    # [3] AI 엔진 호출 (chatbot_logic.py)
    # 가입일(signup_date)이나 루틴 상태 정보를 AI에게 컨텍스트로 전달할 수 있습니다.
    ai_res = get_chat_response(
        user_message=data.message,
        chat_history=chat_history,
        is_onboarding_done=user.is_onboarding_done,
        user_animal=user.user_animal or "",
        signup_date=signup_date  # 유저의 가입 기간에 따른 대화 차별화 가능
    )

    if not ai_res:
        raise HTTPException(status_code=500, detail="AI 응답 생성에 실패했습니다.")

    # [4] 데이터베이스 저장 로직 (핵심 수정 구간)
    
    # (1) 사용자가 보낸 답변 저장 (created_at은 DB에서 자동 생성됨)
    db.add(models.ChatHistory(user_id=data.user_id, role="user", content=data.message))
    
    # (2) AI의 응답 저장 방식 결정
    if ai_res.get("is_finished"):
        # 테스트가 완전히 끝났을 때: 유저 정보 업데이트
        user.is_onboarding_done = True
        user.user_animal = ai_res.get("result_name")
        user.assigned_category = ai_res.get("category")
        
        reply_for_db = f"진단 완료: {ai_res.get('result_name')} ({ai_res.get('category')})"
        
        # [C의 로직 반영] 온보딩 종료 시점에 첫 루틴을 할당하는 등의 로직 연동 가능
        # routine_manager.initialize_user_routine(user.id, user.assigned_category)
    
    elif "type" in ai_res and ai_res.get("type") == "select":
        # 질문 진행 중일 때 JSON 객체 저장
        reply_for_db = json.dumps(ai_res, ensure_ascii=False)
        
    else:
        # 일반 상담 모드
        reply_for_db = ai_res.get("reply_message", "알 수 없는 응답입니다.")

    # AI 응답을 DB에 최종 추가
    # [요구사항 2 반영] models.py 설정에 의해 timezone-aware한 시간이 기록됩니다.
    db.add(models.ChatHistory(user_id=data.user_id, role="assistant", content=reply_for_db))
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"DB 저장 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터 저장 중 오류가 발생했습니다.")

    # [5] 프론트엔드 응답 시 signup_date 등 추가 정보 포함 (필요 시)
    ai_res["signup_date"] = signup_date.isoformat() if signup_date else None
    
    return ai_res