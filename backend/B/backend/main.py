from fastapi import FastAPI
from database import engine, SessionLocal
import models
from routers import user, diary, analysis, survey

# 테이블 자동 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Router 등록
app.include_router(user.router)
app.include_router(diary.router)
app.include_router(analysis.router)
app.include_router(survey.router)


@app.get("/api/result")
def get_result():

    db = SessionLocal()

    try:
        result = db.query(models.Analysis).all()
        return result
    finally:
        db.close()