from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from sqlalchemy.orm import Session
from services.chatbot_logic import get_chat_response # 담당 A의 로직
import models
from pydantic import BaseModel

router = APIRouter()

# --- [1. 요청 데이터 모델] ---
class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/api/chat")
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    """
    사용자와 챗봇(토끼) 간의 대화를 처리하고, 
    온보딩 종료 시 유저에게 동물 캐릭터와 질환 카테고리를 부여합니다.
    """
    # 1. 유저 확인
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 2. 과거 대화 내역 조회 (AI에게 문맥을 전달하기 위함)
    history_objs = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.user_id == data.user_id)\
        .order_by(models.ChatHistory.created_at.asc())\
        .all()
    
    chat_history = [{"role": h.role, "content": h.content} for h in history_objs]

    # 3. AI 응답 생성 (A의 로직 호출)
    # 온보딩 상태와 현재 동물 정보를 함께 전달하여 맞춤형 대화 유도
    ai_res = get_chat_response(
        user_message=data.message,
        chat_history=chat_history,
        is_onboarding_done=user.is_onboarding_done,
        user_animal=user.user_animal or ""
    )

    if not ai_res:
        raise HTTPException(status_code=500, detail="AI 응답 생성에 실패했습니다.")

    # 4. DB 업데이트 (메시지 저장)
    # 사용자가 보낸 메시지 저장
    db.add(models.ChatHistory(user_id=data.user_id, role="user", content=data.message))
    
    # AI 응답 내용 결정 및 저장
    if ai_res.get("is_finished"):
        # 온보딩이 완료된 경우
        user.is_onboarding_done = True
        user.user_animal = ai_res.get("result_name") # 예: "정리대장 펭귄"
        
        # [중요] 이후 정밀 설문 연동을 위해 질환 카테고리 코드 저장
        # ai_logic.py나 chatbot_logic.py에서 넘어온 category (예: "OCD") 저장
        user.assigned_category = ai_res.get("category") 
        
        reply_content = f"진단을 마쳤습니다! 당신은 '{user.user_animal}' 유형입니다. 이제 당신에게 맞는 정밀 설문을 시작해볼까요?"
    else:
        reply_content = ai_res.get("reply_message")
    
    # 챗봇(assistant)의 응답 저장
    db.add(models.ChatHistory(user_id=data.user_id, role="assistant", content=reply_content))
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="대화 내용 저장 중 오류가 발생했습니다.")

    # 프론트엔드에 AI 결과 전체 전달
    return {
        "reply_message": reply_content,
        "is_finished": ai_res.get("is_finished"),
        "user_animal": user.user_animal,
        "assigned_category": user.assigned_category
    }