from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from services.chatbot_logic import get_chat_response
from pydantic import BaseModel
import json

# 1. 프론트엔드로부터 받을 데이터 규격
class ChatRequest(BaseModel):
    user_id: str
    message: str

router = APIRouter()

@router.post("/api/chat")
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    # [1] 사용자 확인
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # [2] 과거 대화 내역 불러오기 (최근 20개 정도면 충분합니다)
    history_objs = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.user_id == data.user_id)\
        .order_by(models.ChatHistory.created_at.asc())\
        .all()
    
    # DB에 저장된 대화 기록을 AI가 읽을 수 있는 리스트 형식으로 변환
    chat_history = []
    for h in history_objs:
        chat_history.append({"role": h.role, "content": h.content})

    # [3] AI 엔진 호출 (chatbot_logic.py)
    ai_res = get_chat_response(
        user_message=data.message,
        chat_history=chat_history,
        is_onboarding_done=user.is_onboarding_done,
        user_animal=user.user_animal or ""
    )

    if not ai_res:
        raise HTTPException(status_code=500, detail="AI 응답 생성에 실패했습니다.")

    # [4] 데이터베이스 저장 로직 (핵심 수정 구간)
    
    # (1) 사용자가 보낸 답변 저장
    db.add(models.ChatHistory(user_id=data.user_id, role="user", content=data.message))
    
    # (2) AI의 응답 저장 방식 결정
    if ai_res.get("is_finished"):
        # 테스트가 완전히 끝났을 때: 유저 정보 업데이트 및 결과 텍스트 저장
        user.is_onboarding_done = True
        user.user_animal = ai_res.get("result_name")
        user.assigned_category = ai_res.get("category")
        
        reply_for_db = f"진단 완료: {ai_res.get('result_name')} ({ai_res.get('category')})"
    
    elif "type" in ai_res and ai_res.get("type") == "select":
        # 질문 진행 중일 때: [매우 중요] JSON 객체 전체를 문자열로 저장!
        # 이렇게 저장해야 다음 호출 때 GPT가 '1번 질문'을 이미 했다는 것을 정확히 기억합니다.
        reply_for_db = json.dumps(ai_res, ensure_ascii=False)
        
    else:
        # 일반 상담 모드일 때
        reply_for_db = ai_res.get("reply_message", "알 수 없는 응답입니다.")

    # AI 응답을 DB에 최종 추가
    db.add(models.ChatHistory(user_id=data.user_id, role="assistant", content=reply_for_db))
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"DB 저장 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터 저장 중 오류가 발생했습니다.")

    # [5] 프론트엔드에는 파싱된 JSON 객체 그대로 전달
    return ai_res