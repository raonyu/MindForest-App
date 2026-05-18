from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db
import models, uvicorn
# [수정] 우리가 업데이트한 라우터들을 임포트합니다.
from routers import user, diary, analysis, survey, chatbot, animal, routines

# 1. DB 테이블 자동 생성 및 스키마 업데이트
# 요구사항 1(필드 추가)과 2(타임존)가 반영된 models.py를 기준으로 테이블을 생성/업데이트합니다.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="마음의 숲 (Mind Forest) API",
    description="9대 정신질환 맞춤형 동물 캐릭터 심리 상담 및 루틴 관리 서비스",
    version="1.1.0"
)

# 2. CORS 설정
# 프론트엔드(React/Vue 등)와의 원활한 데이터 송수신을 위한 설정입니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Router 등록
# 조원 B와 C의 로직이 연동된 라우터들을 하위 경로로 등록합니다.
app.include_router(user.router, prefix="/api/user", tags=["User & Auth"])
app.include_router(diary.router, prefix="/api/diary", tags=["Diary & Emotion"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis & Report"])
app.include_router(survey.router, prefix="/api/survey", tags=["Clinical Survey"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Onboarding Chatbot"])
app.include_router(animal.router, prefix="/api/animal", tags=["Animals"])
app.include_router(routines.router, prefix="/api/routines", tags=["Routines"])

# 4. 서비스 헬스 체크용 엔드포인트
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Mind Forest API! 🌲",
        "status": "Running",
        "timezone_mode": "UTC (Timezone-aware)"
    }

# 5. [관리자용] 전체 데이터 확인 (테스트 단계용)
@app.get("/api/admin/check-schema", tags=["Admin"])
def check_schema(db: Session = Depends(get_db)):
    """
    Diary 테이블에 routine_category와 score_diff가 잘 들어갔는지 
    최근 데이터 1개를 샘플로 확인합니다.
    """
    sample = db.query(models.Diary).order_by(models.Diary.id.desc()).first()
    if not sample:
        return {"message": "데이터가 없습니다."}
    
    return {
        "id": sample.id,
        "routine_category": sample.routine_category,
        "score_diff": sample.score_diff,
        "created_at": sample.created_at
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)