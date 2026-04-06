from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models  
from database import engine, get_db  
from analysis_C import get_mind_forest_report  
# [추가] 새로 만든 루틴 매니저 불러오기
from routine_manager import get_recommended_routines  
import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="마음의 숲(MindForest) 통합 API - 담당 C 김예영",
    description="심리 지표 분석 및 개인 맞춤형 루틴 추천 서비스를 제공합니다."
)

# 1. 기존 심리 지표 리포트 엔드포인트
@app.get("/api/analysis/report/{user_id}")
def generate_report(user_id: str, db: Session = Depends(get_db)):
    try:
        report_data = get_mind_forest_report(db, user_id)
        if "error" in report_data:
            raise HTTPException(status_code=404, detail=report_data["error"])
        return report_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 엔진 구동 실패: {str(e)}")

# 2. [신규] 개인 맞춤형 루틴 추천 엔드포인트
@app.get("/api/routine/recommend/{user_id}")
def recommend_routine(user_id: str, db: Session = Depends(get_db)):
    """
    사용자의 가입일과 과거 로그를 분석하여 오늘 수행할 루틴 3개를 추천합니다.
    """
    try:
        # DB에서 유저 정보와 로그 가져오기 (B파트 연동 부분)
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 추천 엔진에 넘겨줄 데이터 포맷팅
        # (실제 서비스 시 user.logs 등을 연동해야 함)
        user_data = {
            'signup_date': user.created_at.date(), 
            'logs': [] # 실제로는 DB의 루틴 수행 이력을 쿼리해서 넣어야 함
        }
        
        # 담당 C의 루틴 추천 엔진 실행
        recommendations = get_recommended_routines(user_data)
        
        return {"today_routines": recommendations}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"루틴 추천 실패: {str(e)}")

@app.get("/api/analysis/check")
def health_check():
    return {
        "status": "ready",
        "developer": "Kim Ye-young",
        "target": "University of Ulsan Team Project",
        "features": ["Mental Report", "Routine Recommendation"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)