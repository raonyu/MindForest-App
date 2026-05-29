from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import ChatHistory
from pydantic import BaseModel
from typing import List
import datetime

router = APIRouter()

class ChatMessageOut(BaseModel):
    id: int
    role: str  # sender role (e.g., "user" or "bot")
    content: str
    timestamp: str  # ISO‑8601 string

    class Config:
        orm_mode = True

class ChatHistoryResponse(BaseModel):
    user_id: str
    total: int
    limit: int
    offset: int
    messages: List[ChatMessageOut]

@router.get(
    "/api/chat/history",
    response_model=ChatHistoryResponse,
    tags=["Chat History"],
    summary="지난 30일 동안 사용자의 채팅 메시지를 오래된 순서대로 가져옵니다",

)
def get_chat_history(
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    # Insert existing auth dependency here if the project uses one, e.g. token: str = Depends(auth.verify_token)
):
    """마지막 30일 간의 채팅 메시지를 가져옵니다.

    1. `user_id` 로 필터링합니다.
    2. `created_at` 을 최근 30일 내로 제한합니다.
    3. `created_at` 을 오름차순(오래된 순)으로 정렬합니다.
    4. 페이지네이션(`limit`/`offset`)을 적용합니다.
    5. 30일 기간의 전체 개수와 현재 슬라이스된 리스트를 반환합니다.
    """

    # 선택 사항: 인증을 강제하려면 토큰 사용자와 `user_id` 가 일치하는지 확인하고, 다르면 403 오류를 반환합니다.
    # if token_user_id != user_id:
    #     raise HTTPException(status_code=403, detail="Unauthorized")

    thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)

    total = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .filter(ChatHistory.created_at >= thirty_days_ago)
        .count()
    )

    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .filter(ChatHistory.created_at >= thirty_days_ago)
        .order_by(ChatHistory.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    messages = [
        ChatMessageOut(
            id=row.id,
            role=row.role,
            content=row.content,
            timestamp=row.created_at.isoformat(),
        )
        for row in rows
    ]

    return ChatHistoryResponse(
        user_id=user_id,
        total=total,
        limit=limit,
        offset=offset,
        messages=messages,
    )
