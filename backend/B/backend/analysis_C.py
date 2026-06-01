import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import models

MIN_REPORT_DIARIES = 3

def get_mind_forest_report(db: Session, user_id: str):
    # [설정] Pandas Timestamp로 시간 기준 통일 (B의 timezone=True 대응)
    now_dt = datetime.now(timezone.utc)
    now = pd.Timestamp(now_dt)

    # 1. 14일치 데이터 로드 (B의 models.Diary 필드 기준)
    diaries = db.query(models.Diary).filter(
        models.Diary.user_id == user_id,
        models.Diary.created_at >= now_dt - timedelta(days=14)
    ).all()

    if len(diaries) < MIN_REPORT_DIARIES:
        return {"error": "분석할 일기 데이터가 부족합니다."}

    # 2. 데이터 변환 (B의 변수명 반영: is_done 등)
    # ORM 객체에서 내부 필드 제거하고 DataFrame 생성
    df = pd.DataFrame([{k: v for k, v in d.__dict__.items() if not k.startswith("_")} for d in diaries])
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # 3. 감정 및 컬럼 방어 로직
    pos = ["joy", "trust", "anticipation", "surprise"]
    neg = ["sadness", "anger", "fear", "disgust"]
    all_ems = pos + neg
    
    for col in all_ems:
        if col not in df.columns: df[col] = 0.0
    
    if "analysis_comment" not in df.columns: 
        df["analysis_comment"] = ""
    
    # B의 모델 변수명 is_done 확인 (없으면 False 처리)
    if "is_done" not in df.columns:
        df["is_done"] = False

    # 4. 마음 온도(에너지 점수) 산출 및 보정
    df["total_score"] = df[pos].sum(axis=1) - df[neg].sum(axis=1)
    df["temp_val"] = (df["total_score"] + 50).clip(0, 100)

    # 5. 기간별 필터링
    df_7 = df[df["created_at"] >= now - timedelta(days=7)].copy()
    df_3 = df[df["created_at"] >= now - timedelta(days=3)].sort_values("created_at").copy()
    df_last_week = df[(df["created_at"] < now - timedelta(days=7)) & (df["created_at"] >= now - timedelta(days=14))].copy()

    # ---------------------------------------------------------
    # #1 주간 지배 감정 (이모지 매핑)
    emoji_map = {
        "joy": "😊", "sadness": "😢", "anger": "😡", "fear": "😨", 
        "trust": "🤝", "surprise": "😲", "disgust": "🤮", "anticipation": "⏳"
    }
    top_emo = df_7[all_ems].mean().idxmax() if not df_7.empty else "joy"
    
    # #2 현재 마음 온도 및 지난주 대비 변화
    this_avg = df_7["temp_val"].mean() if not df_7.empty else 50.0
    last_avg = df_last_week["temp_val"].mean() if not df_last_week.empty else this_avg
    diff = round(this_avg - last_avg, 1)

    # #5 루틴 효능 랭킹: 프론트가 기대하는 [{ routine, effect }] 형태로 반환
    if "routine_name" not in df.columns:
        df["routine_name"] = ""
    df_routine = df[df["routine_name"].fillna("").str.strip() != ""]
    routine_rank = []
    if not df_routine.empty:
        routine_effects = (
            df_routine.groupby("routine_name")["temp_val"]
            .mean()
            .sort_values(ascending=False)
            .head(3)
        )
        routine_rank = [
            {"routine": str(routine), "effect": round(float(effect), 1)}
            for routine, effect in routine_effects.items()
        ]

    # #9 레드존 탐지 (Slope 계산)
    red_points = []
    if len(df_3) >= 2:
        time_diff = df_3["created_at"].diff().dt.total_seconds() / 3600
        time_diff = time_diff.replace(0, np.nan)
        df_3["slope"] = df_3["temp_val"].diff() / time_diff
        red_points = [
            int(row.created_at.day)
            for row in df_3[df_3["slope"] < -20].itertuples()
        ]

    # #10 AI vs 사용자 간극 (B의 Analysis 모델 연동)
    ai_record = db.query(models.Analysis).join(models.Diary).filter(models.Diary.user_id == user_id).order_by(models.Analysis.id.desc()).first()
    ai_val = ai_record.score if ai_record else 50.0

    # ---------------------------------------------------------
    # 최종 결과 반환 (1번~12번 지표 통합)

    
    keywords = (
        df_7["analysis_comment"]
        .fillna("")
        .str.split(",")
        .explode()
        .str.strip()
        .replace("", np.nan)
        .dropna()
        .value_counts()
        .head(3)
        .index
        .tolist()
    )
    crisis_risk = round(max(0, 100 - this_avg), 1)
    trend_points = df_7[["created_at", "temp_val"]].sort_values("created_at").copy()
    trend_points["created_at"] = trend_points["created_at"].dt.strftime("%Y-%m-%d")

    return {
        "indicator_1": {"report_explain": emoji_map.get(top_emo, "😐"),
                        "report_value": emoji_map.get(top_emo, "😐")},
        "indicator_2": {"report_explain": f"현재 마음 온도는 {round(this_avg, 1)}도 지난주보다 {abs(diff)}도 {'높아졌어요' if diff >= 0 else '낮아졌어요'}",
                        "report_value": {"temp": f"{round(this_avg, 1)}", "msg": f"{abs(diff)}"}},
        "indicator_3": {"report_explain": "최근 7일간 마음 온도 흐름입니다.",
                        "report_value": trend_points.to_dict("records")},
        "indicator_4": {"report_explain": f"루틴과 기록을 바탕으로 회복 탄력성이 {round(this_avg, 1)}%로 나타납니다.",
                        "report_value": f"{round(this_avg, 1)}%"},
        "indicator_5": {"report_explain": "최근 기록에서 확인된 루틴별 평균 마음 온도입니다.",
                        "report_value": routine_rank},
        "indicator_6": {"report_explain": f"14일 중 {df['created_at'].dt.date.nunique()}일 기록 성공",
                        "report_value": f"{df['created_at'].dt.date.nunique()}"},
        "indicator_7": {"report_explain": f"루틴 수행 여부에 따라 에너지가 {abs(diff)}도 변화하는 패턴이 확인됩니다.",
                        "report_value": f"{abs(diff)}"},
        "indicator_8": {"report_explain": f"🛡️ 이번 주 {len(red_points)}번의 급격한 감정 하락 방어",
                        "report_value": f"{len(red_points)}"},
        "indicator_9": {"report_explain": f"🔴 {red_points}개의 레드존 포인트가 감지되었습니다.",
                        "report_value": red_points},
        "indicator_10": {"report_explain": f"사용자님의 감정점수는 AI 예측과 {round(abs(this_avg - ai_val), 1)}도 차이가 나요.",
                        "report_value": {"user": round(this_avg, 1), "ai": ai_val, "gap": round(abs(this_avg - ai_val), 1)}},
        "indicator_11": {"report_explain": "이번 주 기록에서 자주 드러난 키워드입니다.",
                         "report_value": keywords},
        "indicator_12": {"report_explain": f"현재 패턴 유지 시 위기 도달 확률은 {crisis_risk}%입니다.",
                         "report_value": f"{crisis_risk}"}
    }
