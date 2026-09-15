import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import models

MIN_REPORT_DIARIES = 3

POS_EMOTIONS = ["joy", "trust", "anticipation", "surprise"]
NEG_EMOTIONS = ["sadness", "anger", "fear", "disgust"]
ALL_EMOTIONS = POS_EMOTIONS + NEG_EMOTIONS


def self_report_to_score(row):
    """
    사용자 Self-Report를 내부 비교용 0~100 마음 점수로 변환.
    AI 점수를 수정하는 용도가 아니라 indicator_10 비교용.
    """
    scores = []

    pairs = [
        (row.get("emotion"), row.get("emotion_intensity")),
        (row.get("secondary_emotion"), row.get("secondary_emotion_intensity")),
    ]

    for emotion, intensity in pairs:
        if not emotion or pd.isna(intensity):
            continue

        try:
            intensity = max(1.0, min(float(intensity), 5.0))
        except (TypeError, ValueError):
            continue

        if emotion in POS_EMOTIONS:
            score = 50 + intensity * 10
        elif emotion in NEG_EMOTIONS:
            score = 50 - intensity * 10
        else:
            continue

        scores.append(score)

    if not scores:
        return None

    return round(float(np.mean(scores)), 1)


def calculate_recovery_index(df):
    """
    감정 온도가 하락한 뒤 다음 기록에서 얼마나 회복했는지 계산.
    임상적 회복탄력성 척도가 아니라 서비스 내부 '회복 지수'.
    """
    ordered = df.sort_values("created_at").reset_index(drop=True)

    recovery_ratios = []

    for i in range(1, len(ordered) - 1):
        previous_temp = float(ordered.loc[i - 1, "temp_val"])
        current_temp = float(ordered.loc[i, "temp_val"])
        next_temp = float(ordered.loc[i + 1, "temp_val"])

        drop = previous_temp - current_temp

        if drop <= 0:
            continue

        rebound = next_temp - current_temp
        ratio = rebound / drop

        ratio = max(0.0, min(ratio, 1.0))
        recovery_ratios.append(ratio)

    if not recovery_ratios:
        return None

    return round(float(np.mean(recovery_ratios) * 100), 1)


def get_mind_forest_report(db: Session, user_id: str):

    now_dt = datetime.now(timezone.utc)
    now = pd.Timestamp(now_dt)

    # ---------------------------------------------------------
    # 1. 최근 14일 일기
    # ---------------------------------------------------------

    diaries = (
        db.query(models.Diary)
        .filter(
            models.Diary.user_id == user_id,
            models.Diary.created_at >= now_dt - timedelta(days=14),
        )
        .all()
    )

    if len(diaries) < MIN_REPORT_DIARIES:
        return {"error": "분석할 일기 데이터가 부족합니다."}

    df = pd.DataFrame(
        [
            {k: v for k, v in diary.__dict__.items() if not k.startswith("_")}
            for diary in diaries
        ]
    )

    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # ---------------------------------------------------------
    # 2. 필요한 컬럼 방어
    # ---------------------------------------------------------

    for col in ALL_EMOTIONS:
        if col not in df.columns:
            df[col] = 0.0

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    if "analysis_comment" not in df.columns:
        df["analysis_comment"] = ""

    if "is_done" not in df.columns:
        df["is_done"] = False

    if "routine_name" not in df.columns:
        df["routine_name"] = ""

    if "score_diff" not in df.columns:
        df["score_diff"] = 0.0

    # ---------------------------------------------------------
    # 3. AI 마음 온도
    # ---------------------------------------------------------

    df["pos_avg"] = df[POS_EMOTIONS].mean(axis=1)
    df["neg_avg"] = df[NEG_EMOTIONS].mean(axis=1)

    df["temp_val"] = (
        50 + (df["pos_avg"] - df["neg_avg"]) / 2
    ).clip(0, 100)

    # ---------------------------------------------------------
    # 4. 기간 분리
    # ---------------------------------------------------------

    df_7 = df[
        df["created_at"] >= now - timedelta(days=7)
    ].copy()

    df_3 = (
        df[df["created_at"] >= now - timedelta(days=3)]
        .sort_values("created_at")
        .reset_index(drop=True)
        .copy()
    )

    df_last_week = df[
        (df["created_at"] < now - timedelta(days=7))
        & (df["created_at"] >= now - timedelta(days=14))
    ].copy()

    # ---------------------------------------------------------
    # indicator 1 - 주간 지배 감정
    # 최신 라벨링에서 neutral(all-zero) 데이터가 추가될 수 있으므로
    # 모든 감정이 기준점 50 미만이면 neutral로 처리
    # ---------------------------------------------------------

    emoji_map = {
        "joy": "😊",
        "sadness": "😢",
        "anger": "😡",
        "fear": "😨",
        "trust": "🤝",
        "surprise": "😲",
        "disgust": "🤮",
        "anticipation": "⏳",
        "neutral": "😐",
    }

    if df_7.empty:
        top_emo = "neutral"
    else:
        weekly_emotion_avg = df_7[ALL_EMOTIONS].mean()

        max_emotion = weekly_emotion_avg.idxmax()
        max_score = float(weekly_emotion_avg.max())

        # 50점 미만이면 모델이 명확한 감정을 검출하지 못한 것으로 처리
        top_emo = max_emotion if max_score >= 50 else "neutral"

    # ---------------------------------------------------------
    # indicator 2, 3 - 마음 온도
    # ---------------------------------------------------------

    this_avg = (
        float(df_7["temp_val"].mean())
        if not df_7.empty
        else 50.0
    )

    last_avg = (
        float(df_last_week["temp_val"].mean())
        if not df_last_week.empty
        else this_avg
    )

    diff = round(this_avg - last_avg, 1)

    trend_points = (
        df_7[["created_at", "temp_val"]]
        .sort_values("created_at")
        .copy()
    )

    trend_points["temp_val"] = trend_points["temp_val"].round(1)
    trend_points["created_at"] = (
        trend_points["created_at"].dt.strftime("%Y-%m-%d")
    )

    # ---------------------------------------------------------
    # indicator 4 - 회복 지수
    # ---------------------------------------------------------

    recovery_index = calculate_recovery_index(df_7)

    if recovery_index is None:
        recovery_explain = (
            "최근 기록에는 회복 지수를 계산할 "
            "하락-회복 구간이 충분하지 않습니다."
        )
        recovery_value = None
    else:
        recovery_explain = (
            f"최근 감정 하락 이후 회복 정도를 기준으로 "
            f"회복 지수는 {recovery_index}%입니다."
        )
        recovery_value = f"{recovery_index}%"

    # ---------------------------------------------------------
    # indicator 5 - 루틴별 평균 효과
    # ---------------------------------------------------------

    completed_routines = df[
        (df["routine_name"].fillna("").str.strip() != "")
        & (df["is_done"] == True)
    ].copy()

    routine_rank = []

    if not completed_routines.empty:
        routine_effects = (
            completed_routines
            .groupby("routine_name")["score_diff"]
            .mean()
            .sort_values(ascending=False)
            .head(3)
        )

        routine_rank = [
            {
                "routine": str(routine),
                "effect": round(float(effect), 1),
            }
            for routine, effect in routine_effects.items()
        ]

    # ---------------------------------------------------------
    # indicator 7 - 완료 루틴 평균 변화량
    # ---------------------------------------------------------

    if not completed_routines.empty:
        routine_avg_change = round(
            float(completed_routines["score_diff"].mean()), 1
        )
    else:
        routine_avg_change = 0.0

    # ---------------------------------------------------------
    # indicator 8, 9 - 급격한 하락 및 회복
    # ---------------------------------------------------------

    red_points = []
    recovery_after_red = 0

    if len(df_3) >= 2:

        time_diff = (
            df_3["created_at"]
            .diff()
            .dt.total_seconds()
            / 3600
        )

        time_diff = time_diff.replace(0, np.nan)

        df_3["slope"] = (
            df_3["temp_val"].diff() / time_diff
        )

        red_indexes = df_3.index[
            df_3["slope"] < -20
        ].tolist()

        for idx in red_indexes:

            red_points.append(
                int(df_3.loc[idx, "created_at"].day)
            )

            # 급격한 하락 이후 다음 기록에서 상승하면 회복으로 계산
            if idx + 1 < len(df_3):
                if (
                    df_3.loc[idx + 1, "temp_val"]
                    > df_3.loc[idx, "temp_val"]
                ):
                    recovery_after_red += 1

    # ---------------------------------------------------------
    # indicator 10 - 사용자 Self Report vs AI
    # ---------------------------------------------------------

    latest_row = (
        df.sort_values("created_at", ascending=False)
        .iloc[0]
    )

    ai_val = round(float(latest_row["temp_val"]), 1)
    user_val = self_report_to_score(latest_row)

    if user_val is None:

        gap = None

        gap_explain = (
            "최근 기록에 사용자 감정 자가보고가 없어 "
            "AI 분석과의 차이를 계산하지 않았습니다."
        )

        gap_value = {
            "user": None,
            "ai": ai_val,
            "gap": None,
        }

    else:

        gap = round(abs(user_val - ai_val), 1)

        gap_explain = (
            f"사용자 자가보고와 AI 감정지수는 "
            f"{gap}점 차이가 납니다."
        )

        gap_value = {
            "user": user_val,
            "ai": ai_val,
            "gap": gap,
        }

    # ---------------------------------------------------------
    # indicator 11 - 키워드
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # indicator 12 - 주의 지수
    # ---------------------------------------------------------

    attention_index = round(
        max(0.0, min(100.0, 100 - this_avg)),
        1,
    )

    # ---------------------------------------------------------
    # 최종 반환
    # ---------------------------------------------------------

    return {

        "indicator_1": {
            "report_explain": emoji_map.get(top_emo, "😐"),
            "report_value": emoji_map.get(top_emo, "😐"),
        },

        "indicator_2": {
            "report_explain":
                f"현재 마음 온도는 {round(this_avg, 1)}도이며 "
                f"지난주보다 {abs(diff)}도 "
                f"{'높아졌어요' if diff >= 0 else '낮아졌어요'}.",

            "report_value": {
                "temp": f"{round(this_avg, 1)}",
                "msg": f"{abs(diff)}",
            },
        },

        "indicator_3": {
            "report_explain":
                "최근 7일간 마음 온도 흐름입니다.",

            "report_value":
                trend_points.to_dict("records"),
        },

        "indicator_4": {
            "report_explain": recovery_explain,
            "report_value": recovery_value,
        },

        "indicator_5": {
            "report_explain":
                "완료한 루틴별 평균 마음 온도 변화입니다.",

            "report_value":
                routine_rank,
        },

        "indicator_6": {
            "report_explain":
                f"14일 중 "
                f"{df['created_at'].dt.date.nunique()}일 기록 성공",

            "report_value":
                f"{df['created_at'].dt.date.nunique()}",
        },

        "indicator_7": {
            "report_explain":
                f"완료한 루틴 이후 마음 온도는 평균 "
                f"{routine_avg_change:+.1f}점 변화했습니다.",

            "report_value":
                f"{routine_avg_change}",
        },

        "indicator_8": {
            "report_explain":
                f"🛡️ 이번 주 급격한 감정 하락 이후 "
                f"{recovery_after_red}번 회복했습니다.",

            "report_value":
                f"{recovery_after_red}",
        }

        "indicator_9": {
            "report_explain":
                f"🔴 {len(red_points)}개의 레드존 포인트가 "
                f"감지되었습니다.",

            "report_value":
                red_points,
        },

        "indicator_10": {
            "report_explain":
                gap_explain,

            "report_value":
                gap_value,
        },

        "indicator_11": {
            "report_explain":
                "이번 주 기록에서 자주 드러난 키워드입니다.",

            "report_value":
                keywords,
        },

        "indicator_12": {
            "report_explain":
                f"현재 마음 상태를 기준으로 주의 지수는 "
                f"{attention_index}점입니다.",

            "report_value":
                f"{attention_index}",
        },
    }