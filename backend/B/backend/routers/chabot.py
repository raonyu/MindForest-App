# routers/chatbot.py 신규/수정
from fastapi import APIRouter, Depends
from database import get_db
from sqlalchemy.orm import Session
from services.chatbot_logic import get_chat_response # 담당 A의 파일
import models

router = APIRouter()

@router.post("/api/chat")
def chat(user_id: str, message: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    # 1. 과거 대화 조회 (role과 content만 추출하여 리스트화)
    history_objs = db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user_id).order_by(models.ChatHistory.created_at.asc()).all()
    chat_history = [{"role": h.role, "content": h.content} for h in history_objs]

    # 2. AI 호출 (A의 함수 규격에 맞춰 데이터 전달)
    ai_res = get_chat_response(
        user_message=message,
        chat_history=chat_history,
        is_onboarding_done=user.is_onboarding_done,
        user_animal=user.user_animal or ""
    )

    # 3. DB 업데이트 (메시지 저장 및 온보딩 상태 갱신)
    # 유저 메시지 저장
    db.add(models.ChatHistory(user_id=user_id, role="user", content=message))
    
    # AI 응답 저장 및 상태 처리
    if ai_res.get("is_finished"):
        user.is_onboarding_done = True
        user.user_animal = ai_res["result_name"] # 풀네임 저장
        reply_content = f"테스트 완료! 당신은 {ai_res['result_name']}입니다."
    else:
        reply_content = ai_res["reply_message"]
    
    db.add(models.ChatHistory(user_id=user_id, role="assistant", content=reply_content))
    db.commit()

    return ai_res