from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy.orm import Session
from database import engine, get_db, SessionLocal
import models
from routers import user, diary, analysis, survey, chabot

# 테이블 자동 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Router 등록
app.include_router(user.router)
app.include_router(diary.router)
app.include_router(analysis.router)
app.include_router(survey.router)
app.include_router(chabot.router)


@app.get("/api/analysis/results")
def get_result(db: Session = Depends(get_db)): # 의존성 주입!
    return db.query(models.Analysis).all()