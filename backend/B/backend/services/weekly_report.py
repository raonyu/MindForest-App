"""주간 리포트 엔진.

카드마다 필요한 기록의 양이 달라서, 리포트 전체를 한 번에 막지 않고
카드별로 ready / building / insufficient 상태를 따로 계산한다.

설계 원칙
- 기록이 없으면 50점이나 😊 같은 기본값을 만들지 않고 상태로 알린다.
- 감정 점수는 확률이 아니므로 %로 표시하지 않는다(점 단위).
- 상승/하락은 부호를 지운 절댓값이 아니라 direction으로 함께 내려준다.
- 루틴 효과는 "관찰된 평균 차이"이며 인과가 아니다.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

import models
from routine_manager import routine_manager

# --- 감정 분류 -------------------------------------------------------------
# surprise는 긍정/부정 어느 쪽도 아니라서 마음 온도 계산에서 제외한다.
POSITIVE = ("joy", "trust", "anticipation")
NEGATIVE = ("sadness", "anger", "fear", "disgust")
NEUTRAL = ("surprise",)
EMOTIONS = POSITIVE + NEGATIVE + NEUTRAL

EMOTION_LABELS = {
    "joy": "기쁨", "trust": "신뢰", "anticipation": "기대", "surprise": "놀람",
    "sadness": "슬픔", "anger": "분노", "fear": "불안", "disgust": "불쾌",
}
EMOTION_EMOJI = {
    "joy": "😊", "trust": "🤝", "anticipation": "⏳", "surprise": "😲",
    "sadness": "😢", "anger": "😡", "fear": "😨", "disgust": "😖",
}
SURVEY_LABELS = {"DEPRESSION": "우울", "ANXIETY": "불안", "ADHD": "ADHD"}

# --- 카드 상태 -------------------------------------------------------------
READY = "ready"
BUILDING = "building"
INSUFFICIENT = "insufficient"

MSG_INSUFFICIENT = "아직 기록이 충분하지 않아요. 조금 더 기록하면 이 분석을 확인할 수 있어요."

# --- 카드별 최소 기록 기준 --------------------------------------------------
MIN_SPECTRUM = 2        # 주간 대표 감정: 적은 기록으로도 가능
MIN_TREND_DAYS = 4      # 7일 추세: 점이 여러 개 필요
MIN_BASELINE_DAYS = 14  # 개인 기준선: 장기 기록 필요
MIN_RESILIENCE_DAYS = 5 # 회복 탄력성: 하락/회복을 볼 수 있을 만큼
MIN_KEYWORD_DIARIES = 3 # 상황·키워드
MIN_ROUTINE_RECORDS = 3 # 루틴 효과: 같은 루틴 반복 기록
ROUTINE_WINDOW_DAYS = 28

DROP_THRESHOLD = 15.0   # 하루 사이 마음 온도가 이만큼 떨어지면 급락으로 본다
RECOVERY_WINDOW_DAYS = 3
NEGATIVE_ALERT_SCORE = 60.0


def _building_message(more: int) -> str:
    return f"조금 더 기록하면 분석을 시작할 수 있어요. (기록 {more}개 더 필요)"


def _card(status: str, data: Any = None, message: str | None = None, **meta) -> dict:
    card: dict[str, Any] = {"status": status, "data": data, "message": message}
    card.update(meta)
    return card


def _subject_particle(word: str) -> str:
    """받침 여부에 따라 '이/가'를 고른다 (분노가 / 불안이)."""
    if not word:
        return "가"
    last = word[-1]
    if not ("가" <= last <= "힣"):
        return "가"
    return "가" if (ord(last) - 0xAC00) % 28 == 0 else "이"


def _aware(value: datetime) -> datetime:
    """일기 저장 시점에 따라 naive datetime이 섞여 있어 UTC 기준으로 통일한다."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _score(diary, emotion: str) -> float:
    return float(getattr(diary, emotion, 0.0) or 0.0)


def _temperature(diary) -> float:
    """마음 온도: 50을 기준으로 긍정 평균과 부정 평균의 차이를 반영(0~100)."""
    positive = mean(_score(diary, e) for e in POSITIVE)
    negative = mean(_score(diary, e) for e in NEGATIVE)
    return max(0.0, min(100.0, 50 + (positive - negative) / 2))


def _daily_temperatures(diaries) -> list[tuple[Any, float]]:
    """하루에 여러 건이 있으면 평균 내어 (날짜, 온도) 목록으로 만든다."""
    buckets: dict[Any, list[float]] = defaultdict(list)
    for diary in diaries:
        buckets[_aware(diary.created_at).date()].append(_temperature(diary))
    return sorted((day, round(mean(values), 1)) for day, values in buckets.items())


def _direction(delta: float) -> str:
    if delta > 0.05:
        return "up"
    if delta < -0.05:
        return "down"
    return "flat"


def _emotion_means(diaries) -> dict[str, float]:
    if not diaries:
        return {emotion: 0.0 for emotion in EMOTIONS}
    return {
        emotion: round(mean(_score(diary, emotion) for diary in diaries), 1)
        for emotion in EMOTIONS
    }


def _dominant_emotion(diaries) -> str | None:
    if not diaries:
        return None
    means = _emotion_means(diaries)
    top = max(means, key=means.get)
    return top if means[top] > 0 else None


def _emotion_payload(emotion: str, score: float | None = None) -> dict:
    payload = {
        "emotion": emotion,
        "label": EMOTION_LABELS.get(emotion, emotion),
        "emoji": EMOTION_EMOJI.get(emotion, "😐"),
    }
    if score is not None:
        payload["score"] = score
    return payload


# --- 카드 1. 현재 상태 요약 -------------------------------------------------
def _alert_card(week_diaries, baseline, survey) -> dict:
    """주의 단계와 그렇게 판단한 근거를 함께 돌려준다."""
    if not week_diaries:
        return _card(INSUFFICIENT, message=MSG_INSUFFICIENT)

    # 최근 날짜부터 거꾸로, 부정 감정이 높은 날이 며칠 이어졌는지 센다.
    by_day: dict[Any, float] = defaultdict(float)
    for diary in week_diaries:
        day = _aware(diary.created_at).date()
        by_day[day] = max(by_day[day], max(_score(diary, e) for e in NEGATIVE))

    streak = 0
    for _, worst in sorted(by_day.items(), reverse=True):
        if worst >= NEGATIVE_ALERT_SCORE:
            streak += 1
        else:
            break

    if streak >= 5:
        level, message = "HIGH", "요즘 많이 힘드셨겠어요. 전문가와 이야기해 보는 것도 방법이에요."
    elif streak >= 3:
        level, message = "MEDIUM", "며칠째 마음이 무거워 보여요. 오늘은 가볍게 쉬어가도 괜찮아요."
    else:
        level, message = "LOW", "최근 기록은 비교적 안정적인 편이에요."

    evidence: list[str] = []
    if streak >= 2:
        evidence.append(f"부정 감정이 높은 날이 {streak}일 이어졌어요")

    dominant = _dominant_emotion(week_diaries)
    if dominant:
        label = EMOTION_LABELS.get(dominant, dominant)
        evidence.append(f"이번 주에는 {label} 기록이 가장 자주 나타났어요")

    # 개인 기준선 대비 변화(있을 때만)
    if baseline["status"] == READY:
        for item in baseline["data"]["comparisons"]:
            if item["direction"] == "up" and item["delta"] >= 10:
                label = item["label"]
                evidence.append(f"평소보다 {label}{_subject_particle(label)} {item['delta']}점 높아요")
                break

    # 검사 점수 변화(있을 때만)
    if survey["status"] == READY and survey["data"]["direction"] == "up":
        data = survey["data"]
        evidence.append(
            f"{data['label']} 검사 점수가 {data['previous']['score']}점에서 {data['latest']['score']}점으로 올랐어요"
        )

    return _card(
        READY,
        data={
            "level": level,
            "message": message,
            "dominant_emotion": _emotion_payload(dominant) if dominant else None,
            "evidence": evidence,
            "records": len(week_diaries),
        },
    )


# --- 카드 2. 주간 감정 스펙트럼 ---------------------------------------------
def _spectrum_card(week_diaries) -> dict:
    count = len(week_diaries)
    if count == 0:
        return _card(INSUFFICIENT, message=MSG_INSUFFICIENT)
    if count < MIN_SPECTRUM:
        return _card(BUILDING, message=_building_message(MIN_SPECTRUM - count))

    means = _emotion_means(week_diaries)
    ranked = sorted(means.items(), key=lambda item: item[1], reverse=True)
    top3 = [_emotion_payload(emotion, score) for emotion, score in ranked[:3] if score > 0]

    return _card(
        READY,
        data={
            "dominant": top3[0] if top3 else None,
            "top3": top3,
            "distribution": [_emotion_payload(emotion, score) for emotion, score in ranked],
            "records": count,
        },
    )


# --- 카드 3. 마음 온도 + 최근 추이 -------------------------------------------
def _trend_card(week_diaries, prev_week_diaries) -> dict:
    points = _daily_temperatures(week_diaries)
    if len(points) < 2:
        return _card(INSUFFICIENT, message=MSG_INSUFFICIENT)

    current_avg = round(mean(value for _, value in points), 1)
    previous_points = _daily_temperatures(prev_week_diaries)

    comparison = None
    if len(previous_points) >= 2:
        previous_avg = round(mean(value for _, value in previous_points), 1)
        delta = round(current_avg - previous_avg, 1)
        comparison = {
            "previous_avg": previous_avg,
            "delta": abs(delta),
            "direction": _direction(delta),
        }

    data = {
        "current_avg": current_avg,
        "comparison": comparison,
        "points": [{"date": day.isoformat(), "value": value} for day, value in points],
        "days_recorded": len(points),
    }

    if len(points) < MIN_TREND_DAYS:
        # 흐름은 보여주되, 아직 추세로 읽기에는 이르다는 뜻.
        return _card(BUILDING, data=data, message=_building_message(MIN_TREND_DAYS - len(points)))
    return _card(READY, data=data)


# --- 개인 기준선 -------------------------------------------------------------
def _baseline_card(db: Session, user_id: str, week_diaries, week_start: datetime) -> dict:
    """이번 주 감정을 그 사람의 평소 기록과 비교한다."""
    columns = [func.count(models.Diary.id)] + [
        func.avg(getattr(models.Diary, emotion)) for emotion in EMOTIONS
    ]
    row = (
        db.query(*columns)
        .filter(models.Diary.user_id == user_id, models.Diary.created_at < week_start)
        .one()
    )
    past_count = int(row[0] or 0)

    if past_count == 0:
        return _card(INSUFFICIENT, message=MSG_INSUFFICIENT)
    if past_count < MIN_BASELINE_DAYS or not week_diaries:
        return _card(BUILDING, message=_building_message(max(MIN_BASELINE_DAYS - past_count, 1)))

    baseline_means = {emotion: float(row[index + 1] or 0.0) for index, emotion in enumerate(EMOTIONS)}
    week_means = _emotion_means(week_diaries)

    comparisons = []
    for emotion in EMOTIONS:
        delta = round(week_means[emotion] - baseline_means[emotion], 1)
        comparisons.append(
            {
                **_emotion_payload(emotion),
                "week": week_means[emotion],
                "baseline": round(baseline_means[emotion], 1),
                "delta": abs(delta),
                "direction": _direction(delta),
            }
        )
    comparisons.sort(key=lambda item: item["delta"], reverse=True)

    return _card(READY, data={"baseline_days": past_count, "comparisons": comparisons[:3]})


# --- 검사(우울/불안) 점수 추이 ------------------------------------------------
def _survey_card(db: Session, user_id: str, assigned_category: str | None) -> dict:
    query = db.query(models.SurveyResult).filter(models.SurveyResult.user_id == user_id)
    if assigned_category:
        typed = query.filter(models.SurveyResult.survey_type == assigned_category.upper())
        results = typed.order_by(models.SurveyResult.created_at.desc()).limit(2).all()
        if not results:
            results = query.order_by(models.SurveyResult.created_at.desc()).limit(2).all()
    else:
        results = query.order_by(models.SurveyResult.created_at.desc()).limit(2).all()

    if not results:
        return _card(INSUFFICIENT, message="아직 검사 기록이 없어요. 검사를 마치면 변화를 볼 수 있어요.")
    if len(results) < 2:
        return _card(
            BUILDING,
            data={"latest": {"score": results[0].score, "date": _aware(results[0].created_at).date().isoformat()}},
            message="검사를 한 번 더 하면 이전 결과와 비교해 드릴게요.",
        )

    latest, previous = results[0], results[1]
    delta = latest.score - previous.score
    survey_type = (latest.survey_type or "").upper()

    return _card(
        READY,
        data={
            "survey_type": survey_type,
            "label": SURVEY_LABELS.get(survey_type, survey_type or "검사"),
            "latest": {
                "score": latest.score,
                "date": _aware(latest.created_at).date().isoformat(),
                "message": latest.result_message,
            },
            "previous": {
                "score": previous.score,
                "date": _aware(previous.created_at).date().isoformat(),
            },
            "delta": abs(delta),
            "direction": _direction(delta),
            "note": "점수가 오르면 증상이 강해졌다는 뜻이에요.",
        },
    )


# --- 카드 4. 복합 감정 데이 (BWS) --------------------------------------------
def _composite_card(db: Session, user_id: str, since: datetime) -> dict:
    records = (
        db.query(models.BwsRecord)
        .filter(models.BwsRecord.user_id == user_id, models.BwsRecord.created_at >= since)
        .order_by(models.BwsRecord.created_at.desc())
        .all()
    )
    if not records:
        return _card(
            INSUFFICIENT,
            message="최근 기록에서는 감정이 뚜렷하게 갈린 날이 없었어요.",
        )

    days = []
    for record in records:
        candidates = [c.strip() for c in (record.candidates or "").split(",") if c.strip()]
        days.append(
            {
                "date": _aware(record.created_at).date().isoformat(),
                "candidates": [_emotion_payload(c) for c in candidates],
                "best": _emotion_payload(record.best_emotion) if record.best_emotion else None,
                "reasoning": record.reasoning,
            }
        )

    return _card(
        READY,
        data={
            "days": days,
            "note": "여러 감정이 함께 나타난 날이에요. 나쁜 신호가 아니라 마음이 복잡했던 날이라는 뜻이에요.",
        },
    )


# --- 카드 5. 회복 탄력성 -----------------------------------------------------
def _resilience_card(diaries) -> dict:
    points = _daily_temperatures(diaries)
    if len(points) < 2:
        return _card(INSUFFICIENT, message=MSG_INSUFFICIENT)
    if len(points) < MIN_RESILIENCE_DAYS:
        return _card(BUILDING, message=_building_message(MIN_RESILIENCE_DAYS - len(points)))

    events = []
    for index in range(1, len(points)):
        (prev_day, prev_value), (day, value) = points[index - 1], points[index]
        drop = prev_value - value
        if drop < DROP_THRESHOLD:
            continue

        # 급락 이후 정해진 기간 안에 원래 수준 가까이 돌아왔는지 본다.
        recovered_in = None
        for later_day, later_value in points[index + 1:]:
            if (later_day - day).days > RECOVERY_WINDOW_DAYS:
                break
            if later_value >= prev_value - 5:
                recovered_in = (later_day - day).days
                break

        events.append(
            {
                "date": day.isoformat(),
                "from": prev_value,
                "to": value,
                "drop": round(drop, 1),
                "recovered": recovered_in is not None,
                "recovery_days": recovered_in,
            }
        )

    recovered = [event for event in events if event["recovered"]]
    return _card(
        READY,
        data={
            "days_analyzed": len(points),
            "drop_count": len(events),
            "recovered_count": len(recovered),
            "avg_recovery_days": round(mean(e["recovery_days"] for e in recovered), 1) if recovered else None,
            "events": events,
        },
    )


# --- 카드 6. 주요 상황·키워드 -------------------------------------------------
def _keyword_card(diaries) -> dict:
    tagged = [d for d in diaries if (d.keywords or "").strip()]
    if not tagged:
        return _card(INSUFFICIENT, message=MSG_INSUFFICIENT)
    if len(tagged) < MIN_KEYWORD_DIARIES:
        return _card(BUILDING, message=_building_message(MIN_KEYWORD_DIARIES - len(tagged)))

    pairs: Counter = Counter()
    keyword_total: Counter = Counter()
    for diary in tagged:
        dominant = _dominant_emotion([diary])
        for keyword in {k.strip() for k in diary.keywords.split(",") if k.strip()}:
            keyword_total[keyword] += 1
            if dominant:
                pairs[(keyword, dominant)] += 1

    items = [
        {
            "keyword": keyword,
            **_emotion_payload(emotion),
            "count": count,
            "keyword_count": keyword_total[keyword],
        }
        for (keyword, emotion), count in pairs.most_common(5)
    ]
    return _card(READY, data={"items": items, "records": len(tagged)})


# --- 카드 7. 루틴과 감정 변화 -------------------------------------------------
def _routine_card(diaries) -> dict:
    """루틴을 한 날과 하지 않은 날의 마음 온도를 비교한다(인과가 아닌 관찰)."""
    with_routine: dict[str, list[float]] = defaultdict(list)
    without_routine: list[float] = []

    for diary in diaries:
        name = (diary.routine_name or "").strip()
        temperature = _temperature(diary)
        if name:
            with_routine[name].append(temperature)
        else:
            without_routine.append(temperature)

    if not with_routine:
        return _card(INSUFFICIENT, message="루틴을 기록한 날이 아직 없어요.")
    if len(without_routine) < MIN_ROUTINE_RECORDS:
        return _card(
            BUILDING,
            message="루틴을 하지 않은 날의 기록이 더 모이면 비교해 드릴게요.",
        )

    baseline = round(mean(without_routine), 1)
    items = []
    for name, values in with_routine.items():
        average = round(mean(values), 1)
        delta = round(average - baseline, 1)
        items.append(
            {
                "routine": name,
                "average": average,
                "delta": abs(delta),
                "direction": _direction(delta),
                "records": len(values),
                "enough": len(values) >= MIN_ROUTINE_RECORDS,
            }
        )
    items.sort(key=lambda item: (item["enough"], item["average"]), reverse=True)

    status = READY if any(item["enough"] for item in items) else BUILDING
    message = None if status == READY else "같은 루틴을 조금 더 반복하면 비교가 정확해져요."
    return _card(
        status,
        data={
            "baseline_average": baseline,
            "baseline_days": len(without_routine),
            "items": items,
            "note": "루틴을 한 날의 평균 차이일 뿐, 루틴이 원인이라는 뜻은 아니에요.",
        },
        message=message,
    )


# --- 카드 8. 다음 주 맞춤 루틴 -------------------------------------------------
def _next_routine_card(user, week_diaries, alert_card) -> dict:
    try:
        recommendations = routine_manager.get_recommended_routines(user)
    except Exception:
        recommendations = []

    if not recommendations:
        return _card(INSUFFICIENT, message="추천할 루틴을 아직 준비하지 못했어요.")

    dominant = _dominant_emotion(week_diaries)
    level = alert_card["data"]["level"] if alert_card["status"] == READY else "LOW"

    if level in ("MEDIUM", "HIGH"):
        reason = "요즘 마음이 무거운 편이라, 부담이 적은 루틴으로 골랐어요."
    elif dominant in ("sadness", "fear"):
        reason = f"{EMOTION_LABELS.get(dominant, dominant)} 기록이 잦아서, 몸을 움직이거나 쉬어가는 루틴을 골랐어요."
    elif dominant in ("anger", "disgust"):
        reason = f"{EMOTION_LABELS.get(dominant, dominant)} 기록이 있어서, 마음을 가라앉히는 루틴을 골랐어요."
    else:
        reason = "지금 흐름을 이어갈 수 있는 루틴으로 골랐어요."

    return _card(
        READY,
        data={
            "reason": reason,
            "items": [{"content": content} for content in recommendations],
        },
    )


# --- 리포트 조립 ---------------------------------------------------------------
def build_weekly_report(db: Session, user_id: str) -> dict:
    """주간 리포트 카드 묶음을 만든다. 데이터가 없어도 예외 없이 상태로 돌려준다."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return {"status": "no_user", "cards": {}}

    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)
    two_weeks_start = now - timedelta(days=14)
    routine_start = now - timedelta(days=ROUTINE_WINDOW_DAYS)

    recent = (
        db.query(models.Diary)
        .filter(models.Diary.user_id == user_id, models.Diary.created_at >= routine_start)
        .order_by(models.Diary.created_at.asc())
        .all()
    )

    week_diaries = [d for d in recent if _aware(d.created_at) >= week_start]
    prev_week_diaries = [d for d in recent if two_weeks_start <= _aware(d.created_at) < week_start]
    two_week_diaries = [d for d in recent if _aware(d.created_at) >= two_weeks_start]

    baseline = _baseline_card(db, user_id, week_diaries, week_start)
    survey = _survey_card(db, user_id, user.assigned_category)
    summary = _alert_card(week_diaries, baseline, survey)

    cards = {
        "summary": summary,
        "spectrum": _spectrum_card(week_diaries),
        "trend": _trend_card(week_diaries, prev_week_diaries),
        "baseline": baseline,
        "survey_trend": survey,
        "composite_days": _composite_card(db, user_id, two_weeks_start),
        "resilience": _resilience_card(two_week_diaries),
        "keywords": _keyword_card(two_week_diaries),
        "routine_effect": _routine_card(recent),
        "next_routines": _next_routine_card(user, week_diaries, summary),
    }

    recorded_days = len({_aware(d.created_at).date() for d in week_diaries})

    return {
        "status": "ok",
        "generated_at": now.isoformat(),
        "period": {"start": week_start.date().isoformat(), "end": now.date().isoformat(), "days": 7},
        "consistency": {"days_recorded": recorded_days, "days_total": 7},
        "card_status": {key: card["status"] for key, card in cards.items()},
        "cards": cards,
    }
