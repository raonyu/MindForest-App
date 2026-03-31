import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import models

def get_weekly_report(db: Session, user_id: str):
    """
    [담당 C] 지난주 대비 성장률 및 감정 반등 지수 분석 핵심 로직
    - B파트의 Diary 데이터와 연동하여 주간 변화를 추적합니다.
    """
    # 1. DB에서 해당 유저의 모든 일기 데이터 가져오기
    # [수정] SQLAlchemy 쿼리 결과를 Pandas DataFrame으로 변환
    query = db.query(models.Diary).filter(models.Diary.user_id == user_id)
    df = pd.read_sql(query.statement, db.bind)

    # 데이터가 부족할 경우 (최소 2개 이상의 일기 필요)
    if df.empty or len(df) < 2:
        return {
            "growth_rate": 0,
            "rebound_insight": "데이터를 쌓는 중입니다.",
            "comment": "리포트를 생성하려면 이번 주에 최소 2개 이상의 일기 기록이 필요해요!",
            "status": "INSUFFICIENT_DATA"
        }

    # 2. 날짜 데이터 처리 (시간대 Aware 설정 통일)
    df['created_at'] = pd.to_datetime(df['created_at'])
    # 현재 시간을 UTC 기준으로 설정하여 모델과 호환성 유지
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    # 3. [주간 성장률 비교] (지난주 vs 이번주)
    # 이번 주: 오늘부터 7일 전까지
    # 지난 주: 7일 전부터 14일 전까지
    this_week_df = df[(df['created_at'] > one_week_ago) & (df['created_at'] <= now)]
    last_week_df = df[(df['created_at'] > two_weeks_ago) & (df['created_at'] <= one_week_ago)]

    # 평균 joy(기쁨) 점수 비교를 통한 성장률 계산
    this_avg_joy = this_week_df['joy'].mean() if not this_week_df.empty else 0
    last_avg_joy = last_week_df['joy'].mean() if not last_week_df.empty else 0
    
    growth_rate = this_avg_joy - last_avg_joy

    # 4. [감정 반등 지수] 이번 주 중 가장 행복했던 순간 찾기
    if not this_week_df.empty:
        best_day_idx = this_week_df['joy'].idxmax()
        best_day = this_week_df.loc[best_day_idx]
        rebound_date = best_day['created_at'].strftime('%m월 %d일')
        rebound_insight = f"이번 주 {rebound_date}에 가장 긍정적인 반등이 있었어요!"
    else:
        rebound_insight = "이번 주에는 아직 큰 감정 반등이 기록되지 않았어요."

    # 5. [추가 통찰] 부정 감정(슬픔) 감소율 체크
    this_avg_sad = this_week_df['sadness'].mean() if not this_week_df.empty else 0
    last_avg_sad = last_week_df['sadness'].mean() if not last_week_df.empty else 0
    sadness_reduction = last_avg_sad - this_avg_sad

    return {
        "growth_rate": round(growth_rate, 2),
        "sadness_reduction": round(sadness_reduction, 2),
        "rebound_insight": rebound_insight,
        "comment": "마음의 근육이 조금씩 단단해지고 있어요!" if growth_rate > 0 else "잠시 쉬어가도 괜찮은 시기예요.",
        "analysis_date": now.strftime("%Y-%m-%d"),
        "status": "SUCCESS"
    }

def get_personalized_recommendation(category: str):
    """
    [담당 C] 진단된 9가지 질환 카테고리에 따른 맞춤형 행동 가이드
    category: DEPRESSION, ADHD, ANGER 등
    """
    recommendations = {
        "DEPRESSION": "조용히 움츠린 거북이님, 오늘은 5분만 창밖을 보며 광합성 루틴을 해보세요. 비타민 D가 기분 반등에 큰 도움이 됩니다.",
        "BIPOLAR": "알록달록 카멜레온님, 지금의 에너지를 기록으로 남겨보세요. 감정의 파도를 타는 데 일기가 큰 닻이 되어줄 거예요.",
        "ANXIETY": "안절부절 미어캣님, 1분간 눈을 감고 주변의 소리 3가지만 찾아보세요. 현재에 집중하는 감각이 불안을 줄여줍니다.",
        "SCHIZOPHRENIA": "몽환적인 검은 고양이님, 현실의 감각을 깨워줄 따뜻한 차 한 잔을 천천히 마셔보는 건 어떨까요?",
        "PTSD": "상처를 방패 삼은 고슴도치님, 오늘 하루 고생한 나를 위해 가장 편안한 옷을 입고 나만의 안전한 공간에서 쉬어주세요.",
        "OCD": "정리대장 펭귄님, 오늘은 평소보다 조금 덜 완벽해도 괜찮아요. 계획에 없던 작은 일탈 하나를 시도해보세요.",
        "ADHD": "산만한 꼬마 다람쥐님, 오늘은 딱 한 가지 일에만 집중하는 '도토리 집중 시간' 10분을 추천합니다. 타이머를 맞춰보세요!",
        "EATING_DISORDER": "마음을 채우는 판다님, 음식의 맛과 향을 천천히 음미하며 내 몸의 소리에 귀를 기울여보는 시간을 가져봐요.",
        "ANGER": "까칠한 햄스터님, 화가 날 땐 3초간 눈을 감고 심호흡하는 루틴이 평소보다 훨씬 효과적일 거예요."
    }
    
    return recommendations.get(category.upper(), "오늘도 당신의 속도에 맞는 루틴을 응원합니다. 마음의 숲이 함께할게요.")