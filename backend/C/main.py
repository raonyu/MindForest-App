from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models  # 담당 B의 DB 모델 연동
from database import engine, get_db  # 담당 B의 DB 설정 및 세션 연동
from analysis import get_mind_forest_report  # 예영이가 완성한 12지표 분석 로직

# 서버 기동 시 DB 테이블 자동 생성 (B파트 연동 확인)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="마음의 숲(MindForest) 분석 API - 담당 C 김예영",
    description="사용자의 8대 감정 데이터를 분석하여 12가지 심리 지표를 제공합니다."
)

@app.get("/api/analysis/report/{user_id}")
def generate_report(user_id: str, db: Session = Depends(get_db)):
    """
    [1~12번 지표 통합 리포트 생성 엔드포인트]
    담당 A(프론트)가 호출하면 14일간의 데이터를 분석하여 12가지 지표를 반환합니다.
    """
    try:
        # 담당 C의 분석 엔진 실행
        report_data = get_mind_forest_report(db, user_id)
        
        # 데이터가 아예 없는 경우(Error 반환 시) 처리
        if "error" in report_data:
            raise HTTPException(status_code=404, detail=report_data["error"])
            
        return report_data

    except Exception as e:
        # 서버 내부 로직 오류 발생 시 방어 코드
        raise HTTPException(status_code=500, detail=f"분석 엔진 구동 실패: {str(e)}")

@app.get("/api/analysis/check")
def health_check():
    """서버 연결 상태 및 담당자 확인용"""
    return {
        "status": "ready",
        "developer": "Kim Ye-young",
        "target": "University of Ulsan Team Project"
    }

if __name__ == "__main__":
    import uvicorn
    # uvicorn main:app --reload 명령어로 실행 가능
    uvicorn.run(app, host="0.0.0.0", port=8000)