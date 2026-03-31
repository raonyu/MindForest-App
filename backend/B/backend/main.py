from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db
import models
# [수정] 파일명 오타 반영 (chabot -> chatbot)
from routers import user, diary, analysis, survey, chatbot 

# 1. DB 테이블 자동 생성 (개발 단계에서 매우 유용합니다)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="마음의 숲 (Mind Forest) API",
    description="9대 정신질환 맞춤형 동물 캐릭터 심리 상담 서비스",
    version="1.0.0"
)

# 2. CORS 설정 (프론트엔드와 통신하기 위해 반드시 필요합니다!)
# React나 Vue 등 외부에서 API를 호출할 때 발생하는 보안 차단을 막아줍니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 실제 배포 시에는 특정 도메인으로 제한하는 것이 좋습니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Router 등록
# 각 기능별로 태그를 달아주면 /docs(Swagger)에서 보기가 훨씬 편해집니다.
app.include_router(user.router, prefix="/api/user", tags=["User & Auth"])
app.include_router(diary.router, prefix="/api/diary", tags=["Diary & Emotion"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis & Report"])
app.include_router(survey.router, prefix="/api/survey", tags=["Clinical Survey"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Onboarding Chatbot"])

# 4. 서비스 헬스 체크용 엔드포인트
@app.get("/")
def read_root():
    return {"message": "Welcome to Mind Forest API! 🌲🐰"}

# 5. [테스트용] 전체 분석 결과 조회
@app.get("/api/admin/analysis-results", tags=["Admin"])
def get_all_results(db: Session = Depends(get_db)):
    return db.query(models.Analysis).all()