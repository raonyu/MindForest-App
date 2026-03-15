import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models

def get_weekly_report(db: Session, user_id: str):
    """
    담당 C: 지난주 대비 성장률 및 감정 반등 지수 분석 핵심 로직
    """
    # 1. DB에서 해당 유저의 모든 일기/감정 데이터 가져오기 (B파트 연동)
    query = db.query(models.Diary).filter(models.Diary.user_id == user_id)
    df = pd.read_sql(query.statement, db.bind)

    # 데이터가 부족할 경우 예외 처리
    if df.empty or len(df) < 2:
        return {
            "growth_rate": 0,
            "rebound_insight": "데이터를 쌓는 중입니다.",
            "comment": "리포트를 생성하려면 최소 2개 이상의 일기 기록이 필요해요!"
        }

    # 날짜 데이터 처리
    df['created_at'] = pd.to_datetime(df['created_at'])
    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    
    # 2. [실질적 분석 1] 주간 성장률 비교 (지난주 vs 이번주)
    last_week_df = df[df['created_at'] < one_week_ago]
    this_week_df = df[df['created_at'] >= one_week_ago]

    # 지난주 평균 joy 점수와 이번주 평균 비교
    last_avg = last_week_df['joy'].mean() if not last_week_df.empty else 0
    this_avg = this_week_df['joy'].mean()
    growth = this_avg - last_avg

    # 3. [실질적 분석 2] 감정 반등 지수 분석
    # 이번 주 데이터 중 joy(기쁨) 수치가 가장 높았던 날 찾기
    best_day = this_week_df.loc[this_week_df['joy'].idxmax()]
    rebound_date = best_day['created_at'].strftime('%m월 %d일')

    return {
        "growth_rate": round(growth, 2),
        "rebound_insight": f"이번 주 {rebound_date}에 가장 긍정적인 반등이 있었어요!",
        "comment": "지난주보다 점진적으로 마음이 회복되고 있습니다." if growth > 0 else "나를 돌보는 시간이 조금 더 필요해요.",
        "analysis_date": now.strftime("%Y-%m-%d")
    }

def get_personalized_recommendation(user_type: str):
    """
    진단된 사용자 유형(A~I)에 따른 실질적 맞춤형 행동 추천
    """
    recommendations = {
        "A": "거북이님, 오늘은 5분만 창밖을 보며 광합성 루틴을 해보세요. 기분 반등에 큰 도움이 됩니다.",
        "H": "햄스터님, 화가 날 땐 3초간 눈을 감고 심호흡하는 루틴이 평소보다 20% 더 효과적일 거예요.",
        "I": "다람쥐님, 오늘은 딱 한 가지 일에만 집중하는 '도토리 집중 시간' 10분을 추천합니다."
    }
    return recommendations.get(user_type, "오늘도 당신의 속도에 맞는 루틴을 응원합니다.")