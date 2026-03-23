import pandas as pd
import numpy as np
from datetime import timedelta
from sqlalchemy.orm import Session
import models

def get_mind_forest_report(db: Session, user_id: str):
    # [설정] Pandas Timestamp로 시간 기준 통일 (비교 오류 방지)
    now = pd.Timestamp.now(tz="UTC")

    # 14일치 데이터 로드
    diaries = db.query(models.Diary).filter(
        models.Diary.user_id == user_id,
        models.Diary.created_at >= now - timedelta(days=14)
    ).all()

    if not diaries:
        return {"error": "분석할 일기 데이터가 부족합니다."}

    # [수정] 데이터 변환 및 불필요한 ORM 필드 제거
    df = pd.DataFrame([{k: v for k, v in d.__dict__.items() if not k.startswith("_")} for d in diaries])
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # [수정] 감정 및 코멘트 컬럼 방어 (누락 시 0 또는 빈칸 처리)
    pos, neg = ["joy", "trust", "anticipation", "surprise"], ["sadness", "anger", "fear", "disgust"]
    all_ems = pos + neg
    for col in all_ems:
        if col not in df.columns: df[col] = 0
    if "analysis_comment" not in df.columns: df["analysis_comment"] = ""

    # [로직] 종합 에너지 점수 산출 및 0~100 사이 보정
    df["total_score"] = df[pos].sum(axis=1) - df[neg].sum(axis=1)
    df["temp_val"] = (df["total_score"] + 50).clip(0, 100)

    # 기간별 필터링
    df_7 = df[df["created_at"] >= now - timedelta(days=7)].copy()
    df_3 = df[df["created_at"] >= now - timedelta(days=3)].sort_values("created_at").copy()
    df_last_week = df[(df["created_at"] < now - timedelta(days=7)) & (df["created_at"] >= now - timedelta(days=14))].copy()

    # ---------------------------------------------------------
    # #1 주간 지배 감정 (1위 이모지)
    emoji_map = {"joy": "😊", "sadness": "😢", "anger": "😡", "fear": "😨", "trust": "🤝", "surprise": "😲", "disgust": "🤮", "anticipation": "⏳"}
    top_emo = df_7[all_ems].mean().idxmax() if not df_7.empty else "joy"
    
    # #2 현재 마음 온도 (지난주 대비 변화)
    this_avg = df_7["temp_val"].mean() if not df_7.empty else 50
    last_avg = df_last_week["temp_val"].mean() if not df_last_week.empty else this_avg
    diff = round(this_avg - last_avg, 1)

    # #5 루틴 효능 랭킹 (공백 제거 로직 포함)
    df_valid = df[df["analysis_comment"].str.strip() != ""]
    indicator_5 = df_valid.groupby("analysis_comment")["temp_val"].mean().sort_values(ascending=False).head(3).to_dict() if not df_valid.empty else {}

    # #9 레드존 탐지 (Slope 계산 0 방어)
    red_points = []
    if len(df_3) >= 2:
        time_diff = df_3["created_at"].diff().dt.total_seconds() / 3600
        time_diff = time_diff.replace(0, np.nan) # ZeroDivision 방어
        df_3["slope"] = df_3["temp_val"].diff() / time_diff
        red_points = df_3[df_3["slope"] < -20][["created_at", "temp_val"]].to_dict("records")

    # #10 AI vs 사용자 간극
    ai_record = db.query(models.Analysis).join(models.Diary).filter(models.Diary.user_id == user_id).order_by(models.Analysis.id.desc()).first()
    ai_val = ai_record.score if ai_record else 50

    # ---------------------------------------------------------
    # 최종 결과 반환 (1번~12번 지표 통합)
    return {
        "indicator_1": emoji_map.get(top_emo, "😐"),
        "indicator_2": {"temp": f"{round(this_avg, 1)}도", "msg": f"지난주보다 {abs(diff)}도 {'높아졌어요' if diff >= 0 else '낮아졌어요'}"},
        "indicator_3": df_7[["created_at", "temp_val"]].sort_values("created_at").to_dict("records"),
        "indicator_4": f"{round(this_avg, 1)}%",
        "indicator_5": indicator_5,
        "indicator_6": f"14일 중 {df['created_at'].dt.date.nunique()}일 성공",
        "indicator_7": f"루틴 부재 시 에너지가 평소보다 {abs(diff)}도 변화하는 패턴이 보입니다.",
        "indicator_8": f"🛡️ 이번 주 {len(red_points)}번의 위기 방어",
        "indicator_9": red_points,
        "indicator_10": {"user": round(this_avg, 1), "ai": ai_val, "gap": abs(this_avg - ai_val)},
        "indicator_11": df_7["analysis_comment"].fillna("").str.split(",").explode().str.strip().replace("", np.nan).dropna().value_counts().head(3).index.tolist(),
        "indicator_12": f"{round(max(0, 100 - this_avg), 1)}%"
    }