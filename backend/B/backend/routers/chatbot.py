from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from sqlalchemy.orm import Session
# [수정] 임포트 경로를 명확히 하고 중복 임포트를 제거합니다.
from services.chatbot_logic import get_chat_response 
from routine_manager import routine_manager  # 이 부분이 핵심입니다!
import models
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/api/chat")
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    # data.user_id, data.message 형태로 꺼내 사용합니다.
    user_id = data.user_id
    message = data.message

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 1. 과거 대화 조회
    history_objs = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id
    ).order_by(models.ChatHistory.created_at.asc()).all()
    chat_history = [{"role": h.role, "content": h.content} for h in history_objs]

    # 2. AI 호출 (chatbot_logic.py 실행)
    ai_res = get_chat_response(
        user_message=message,
        chat_history=chat_history,
        is_onboarding_done=user.is_onboarding_done
    )

    # 3. 유저 메시지 저장
    db.add(models.ChatHistory(user_id=user_id, role="user", content=message))

    # 4. 온보딩 종료 시 자동 매핑 및 저장
    if ai_res.get("is_finished"):
        category_code = ai_res.get("category", "").strip().upper()
        
        # 유저 상태 업데이트
        user.is_onboarding_done = True
        user.assigned_category = category_code
        
        # 동물 매핑
        animal_info = db.query(models.Animal).filter(models.Animal.category == category_code).first()
        user.user_animal = animal_info.name if animal_info else f"미지의 {category_code}"
        
        # 루틴 자동 생성
        try:
            routine_manager.initialize_user_routine(db, user_id, category_code)
        except Exception as e:
            print(f"루틴 할당 오류: {e}")
            
        reply_content = f"테스트 완료! 당신은 {user.user_animal} 유형입니다. 마이페이지에서 확인해보세요!"
    else:
        reply_content = ai_res.get("reply_message", "계속 말씀해주세요.")

    # 5. AI 응답 저장
    db.add(models.ChatHistory(user_id=user_id, role="assistant", content=reply_content))
    db.commit()

    # 프론트엔드가 받기 편하게 AI 응답 객체 반환
    return ai_res