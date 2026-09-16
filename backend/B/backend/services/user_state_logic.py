from datetime import datetime, timedelta, timezone
import json
import re

from sqlalchemy.orm import Session

import models

POSITIVE_EMOTIONS = ["joy", "trust", "anticipation", "surprise"]
NEGATIVE_EMOTIONS = ["sadness", "anger", "fear", "disgust"]
ALL_EMOTIONS = POSITIVE_EMOTIONS + NEGATIVE_EMOTIONS

SURVEY_NAMES = {
    "DEPRESSION": "PHQ-9",
    "ANXIETY": "GAD-7",
    "ADHD": "ASRS",
    "BIPOLAR": "K-MDQ",
    "PTSD": "PCL-5",
    "OCD": "Y-BOCS",
    "EATING_DISORDER": "EAT-26",
    "ANGER": "DAR-5",
    "SCHIZOPHRENIA": "PRIME-Screen",
}

SURVEY_LINKED_EMOTIONS = {
    "DEPRESSION": ["sadness"],
    "ANXIETY": ["fear"],
    "ADHD": ["anticipation", "surprise"],
    "BIPOLAR": ["joy", "anger", "surprise"],
    "PTSD": ["fear", "sadness"],
    "OCD": ["fear", "disgust"],
    "EATING_DISORDER": ["sadness", "disgust"],
    "ANGER": ["anger"],
    "SCHIZOPHRENIA": ["fear", "surprise"],
}

RISK_PATTERNS = [
    r"죽고\s*싶",
    r"자살",
    r"자해",
    r"사라지고\s*싶",
    r"끝내고\s*싶",
    r"살기\s*싫",
    r"해치고\s*싶",
]


def _as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _round(value, digits=1):
    return round(float(value or 0.0), digits)


def _extract_diary_text(content):
    if not content:
        return ""
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return str(parsed.get("mainText", ""))
    except (TypeError, json.JSONDecodeError):
        pass
    return str(content)


def _mind_temperature(diary):
    pos_avg = sum(float(getattr(diary, emotion, 0.0) or 0.0) for emotion in POSITIVE_EMOTIONS) / len(POSITIVE_EMOTIONS)
    neg_avg = sum(float(getattr(diary, emotion, 0.0) or 0.0) for emotion in NEGATIVE_EMOTIONS) / len(NEGATIVE_EMOTIONS)
    return max(0.0, min(100.0, 50.0 + (pos_avg - neg_avg) / 2.0))


def _survey_level(survey_type, score):
    stype = (survey_type or "").upper()
    score = int(score or 0)

    if stype in ("DEPRESSION", "ANXIETY"):
        if score <= 4:
            return "normal"
        if score <= 9:
            return "mild"
        if score <= 14:
            return "moderate"
        return "high"

    if stype == "ADHD":
        return "high" if score >= 4 else "normal"

    if score <= 10:
        return "normal"
    if score <= 18:
        return "moderate"
    return "high"


def _survey_level_message(level):
    return {
        "normal": "정상 범위",
        "mild": "경미한 수준",
        "moderate": "중간 수준",
        "high": "높은 수준",
    }.get(level, "기록 없음")


def _detect_risk_expressions(diaries):
    matches = []
    for diary in diaries:
        text = _extract_diary_text(diary.content)
        for pattern in RISK_PATTERNS:
            if re.search(pattern, text):
                matches.append({
                    "date": diary.created_at.strftime("%Y-%m-%d") if diary.created_at else None,
                    "pattern": pattern,
                })
                break
    return matches


def _consecutive_negative_days(diaries):
    count = 0
    for diary in sorted(diaries, key=lambda d: _as_utc(d.created_at) or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        negative_peak = max(float(getattr(diary, emotion, 0.0) or 0.0) for emotion in NEGATIVE_EMOTIONS)
        if negative_peak >= 70.0:
            count += 1
        else:
            break
    return count


def _build_empty_state(user_id):
    return {
        "user_id": user_id,
        "emotion_state": "데이터 부족",
        "risk_level": "LOW",
        "level": "LOW",
        "message": "아직 분석할 데이터가 부족해요. 일기를 써서 마음을 기록해보세요!",
        "reasons": ["최근 7일 감정 기록이 부족합니다."],
        "metrics": {
            "diary_count_7d": 0,
            "negative_avg_7d": 0.0,
            "positive_avg_7d": 0.0,
            "mind_temperature_avg_7d": 50.0,
            "mind_temperature_change_7d": 0.0,
            "consecutive_negative_days": 0,
        },
        "latest_survey": None,
        "survey_history": [],
        "survey_emotion_comparison": {
            "status": "no_data",
            "message": "비교할 일기 또는 자가점검 결과가 부족합니다.",
        },
        "safety_flags": [],
    }


def analyze_user_state(db: Session, user_id: str):
    now = datetime.now(timezone.utc)
    since_14 = now - timedelta(days=14)

    diaries = db.query(models.Diary).filter(
        models.Diary.user_id == user_id,
        models.Diary.created_at >= since_14,
    ).order_by(models.Diary.created_at.asc()).all()

    if not diaries:
        return _build_empty_state(user_id)

    recent_7 = [diary for diary in diaries if _as_utc(diary.created_at) and _as_utc(diary.created_at) >= now - timedelta(days=7)]
    if not recent_7:
        recent_7 = diaries[-7:]

    positive_avg = sum(
        sum(float(getattr(diary, emotion, 0.0) or 0.0) for emotion in POSITIVE_EMOTIONS) / len(POSITIVE_EMOTIONS)
        for diary in recent_7
    ) / len(recent_7)
    negative_avg = sum(
        sum(float(getattr(diary, emotion, 0.0) or 0.0) for emotion in NEGATIVE_EMOTIONS) / len(NEGATIVE_EMOTIONS)
        for diary in recent_7
    ) / len(recent_7)

    temperatures = [_mind_temperature(diary) for diary in recent_7]
    temp_avg = sum(temperatures) / len(temperatures)
    temp_change = temperatures[-1] - temperatures[0] if len(temperatures) >= 2 else 0.0
    consecutive_days = _consecutive_negative_days(recent_7)
    safety_flags = _detect_risk_expressions(recent_7)

    # [수정] 전문 진단 설문(PHQ-9/GAD-7/ASRS 등) 최근 30일 기준으로만 조회
    since_30d = now - timedelta(days=30)
    survey_history_rows = db.query(models.SurveyResult).filter(
        models.SurveyResult.user_id == user_id,
        models.SurveyResult.created_at >= since_30d,
    ).order_by(models.SurveyResult.created_at.asc()).all()

    survey_history = [
        {
            "survey_type": row.survey_type,
            "scale_name": SURVEY_NAMES.get((row.survey_type or "").upper(), row.survey_type),
            "score": row.score,
            "level": _survey_level(row.survey_type, row.score),
            "result_message": row.result_message,
            "created_at": row.created_at,
        }
        for row in survey_history_rows
    ]
    latest_survey = survey_history[-1] if survey_history else None
    prev_survey = survey_history[-2] if len(survey_history) >= 2 else None

    # [수정] 같은 설문 유형끼리 이전 검사 대비 점수 변화량(delta) 계산
    score_delta = None
    if (
        latest_survey and prev_survey
        and latest_survey["survey_type"] == prev_survey["survey_type"]
    ):
        score_delta = latest_survey["score"] - prev_survey["score"]
    if latest_survey:
        latest_survey = dict(latest_survey)  # 원본 리스트 영향 방지
        latest_survey["score_delta"] = score_delta

    risk_score = 0
    reasons = []

    if negative_avg >= 70:
        risk_score += 25
        reasons.append("최근 7일 부정 감정 평균이 높은 편입니다.")
    elif negative_avg >= 55:
        risk_score += 15
        reasons.append("최근 7일 부정 감정 평균이 다소 높습니다.")

    if temp_avg <= 35:
        risk_score += 20
        reasons.append("최근 7일 마음 온도 평균이 낮습니다.")
    elif temp_avg <= 45:
        risk_score += 10
        reasons.append("최근 7일 마음 온도 평균이 약간 낮습니다.")

    if temp_change <= -10:
        risk_score += 15
        reasons.append("최근 마음 온도가 뚜렷하게 하락했습니다.")
    elif temp_change <= -5:
        risk_score += 8
        reasons.append("최근 마음 온도가 하락하는 흐름입니다.")

    if consecutive_days >= 7:
        risk_score += 25
        reasons.append("강한 부정 감정이 7일 이상 이어졌습니다.")
    elif consecutive_days >= 3:
        risk_score += 15
        reasons.append("강한 부정 감정이 3일 이상 이어졌습니다.")

    if latest_survey:
        survey_level = latest_survey["level"]
        if survey_level == "high":
            risk_score += 25
            reasons.append(f"최근 {latest_survey['scale_name']} 자가점검 결과가 높은 수준입니다.")
        elif survey_level == "moderate":
            risk_score += 15
            reasons.append(f"최근 {latest_survey['scale_name']} 자가점검 결과가 중간 수준입니다.")
        elif survey_level == "mild":
            risk_score += 8
            reasons.append(f"최근 {latest_survey['scale_name']} 자가점검 결과가 경미한 수준입니다.")

        # [수정] 이전 검사 대비 점수 변화량을 risk_score에 반영
        _delta = latest_survey.get("score_delta")
        if _delta is not None and _delta >= 5:
            risk_score += 10
            reasons.append(
                f"최근 {latest_survey['scale_name']} 점수가 이전 검사 대비 {_delta:+}점 상승했습니다."
            )
        elif _delta is not None and _delta <= -5:
            # 점수 개선은 위험도를 낮추지 않으나 긍정적 변화로 기록
            reasons.append(
                f"최근 {latest_survey['scale_name']} 점수가 이전 검사 대비 {_delta}점 개선됐습니다."
            )

    if safety_flags:
        risk_score += 40
        reasons.append("최근 기록에 즉시 주의가 필요한 위험 표현이 포함되어 있습니다.")

    if safety_flags or risk_score >= 60:
        risk_level = "HIGH"
        message = "최근 기록에서 높은 주의가 필요한 신호가 보여요. 혼자 견디기보다 주변 사람이나 전문가의 도움을 함께 고려해주세요."
    elif risk_score >= 30:
        risk_level = "MEDIUM"
        message = "최근 감정 변화가 이어지고 있어요. 부담이 낮은 루틴과 꾸준한 기록으로 상태를 살펴보는 것이 좋겠습니다."
    else:
        risk_level = "LOW"
        message = "현재 기록에서는 큰 위험 신호가 두드러지지 않습니다. 지금처럼 마음을 꾸준히 기록해보세요."

    # [수정] 감정 상태는 일기 감정 데이터만으로 독립 판단 (위험도와 분리)
    # 감정 강도가 높다고 위험도가 자동으로 HIGH가 되지 않도록 구조 분리
    if safety_flags or consecutive_days >= 3:
        emotion_state = "지속적인 부정적 변화"
    elif negative_avg >= 55 or temp_change <= -5:
        emotion_state = "일시적 감정 변화"
    else:
        emotion_state = "정상"

    if not reasons:
        reasons.append("최근 감정 강도, 지속성, 추세, 자가점검 결과에서 큰 위험 신호가 두드러지지 않습니다.")

    comparison = _compare_survey_and_emotion(latest_survey, recent_7, negative_avg)

    return {
        "user_id": user_id,
        "emotion_state": emotion_state,
        "risk_level": risk_level,
        "level": risk_level,
        "message": message,
        "reasons": reasons,
        "metrics": {
            "diary_count_7d": len(recent_7),
            "negative_avg_7d": _round(negative_avg),
            "positive_avg_7d": _round(positive_avg),
            "mind_temperature_avg_7d": _round(temp_avg),
            "mind_temperature_change_7d": _round(temp_change),
            "consecutive_negative_days": consecutive_days,
            "risk_score": risk_score,
        },
        "latest_survey": latest_survey,
        "survey_history": survey_history,
        "survey_emotion_comparison": comparison,
        "safety_flags": safety_flags,
    }


def _compare_survey_and_emotion(latest_survey, recent_diaries, negative_avg):
    if not latest_survey or not recent_diaries:
        return {
            "status": "no_data",
            "message": "비교할 일기 또는 자가점검 결과가 부족합니다.",
        }

    survey_type = (latest_survey["survey_type"] or "").upper()
    linked_emotions = SURVEY_LINKED_EMOTIONS.get(survey_type, NEGATIVE_EMOTIONS)
    linked_avg = sum(
        sum(float(getattr(diary, emotion, 0.0) or 0.0) for emotion in linked_emotions) / len(linked_emotions)
        for diary in recent_diaries
    ) / len(recent_diaries)

    survey_level = latest_survey["level"]
    survey_is_elevated = survey_level in ("mild", "moderate", "high")
    emotion_is_elevated = linked_avg >= 55 or negative_avg >= 55

    if survey_is_elevated and emotion_is_elevated:
        status = "aligned_elevated"
        message = f"{latest_survey['scale_name']} 결과와 최근 일기 감정 흐름이 비슷하게 주의 신호를 보입니다."
    elif survey_is_elevated and not emotion_is_elevated:
        status = "survey_elevated"
        message = f"{latest_survey['scale_name']} 결과는 주의가 필요하지만 최근 일기 감정은 비교적 안정적입니다."
    elif not survey_is_elevated and emotion_is_elevated:
        status = "emotion_elevated"
        message = "자가점검 결과는 낮지만 최근 일기에서는 부정 감정 상승이 보여 일시적 스트레스 가능성을 살펴볼 필요가 있습니다."
    else:
        status = "aligned_stable"
        message = "자가점검 결과와 최근 일기 감정 흐름 모두 큰 위험 신호가 두드러지지 않습니다."

    return {
        "status": status,
        "linked_emotions": linked_emotions,
        "linked_emotion_avg_7d": _round(linked_avg),
        "message": message,
    }


def build_chat_state_summary(state):
    """GPT 채팅에 주입할 사용자 상태 요약 딕셔너리를 생성합니다."""
    latest_survey = state.get("latest_survey") or {}
    metrics = state.get("metrics") or {}

    # 마음 온도 변화량으로 감정 추세 문자열 결정
    temp_change = metrics.get("mind_temperature_change_7d", 0.0) or 0.0
    if temp_change <= -5:
        emotion_trend = "감소"
    elif temp_change >= 5:
        emotion_trend = "증가"
    else:
        emotion_trend = "유지"

    return {
        "emotion_state": state.get("emotion_state"),
        "risk_level": state.get("risk_level"),
        "reasons": state.get("reasons", [])[:3],
        "latest_survey": {
            "scale_name": latest_survey.get("scale_name"),
            "score": latest_survey.get("score"),
            "level": latest_survey.get("level"),
            # [수정] 이전 검사 대비 점수 변화량 포함
            "score_delta": latest_survey.get("score_delta"),
        } if latest_survey else None,
        "seven_day_summary": {
            "negative_avg": metrics.get("negative_avg_7d"),
            "positive_avg": metrics.get("positive_avg_7d"),
            "mind_temperature_avg": metrics.get("mind_temperature_avg_7d"),
            "mind_temperature_change": temp_change,
            "consecutive_negative_days": metrics.get("consecutive_negative_days"),
            # [수정] 감정 추세 문자열 추가
            "emotion_trend": emotion_trend,
        },
        "safety_flags_count": len(state.get("safety_flags", [])),
    }
