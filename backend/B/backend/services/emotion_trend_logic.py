from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
import models

POSITIVE_EMOTIONS = ["joy", "trust", "anticipation", "surprise"]
NEGATIVE_EMOTIONS = ["sadness", "anger", "fear", "disgust"]
ALL_EMOTIONS = POSITIVE_EMOTIONS + NEGATIVE_EMOTIONS

BASELINE_DAYS = 30
RECENT_DAYS = 7
MIN_BASELINE_RECORDS = 5
MIN_RECENT_RECORDS = 2

FALLBACK_SUDDEN_DROP = 15.0
MIN_BASELINE_DEPARTURE = 8.0
MIN_CHANGE_POINT_DROP = 10.0
RECOVERY_LOOKAHEAD_RECORDS = 3


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _round(value: Optional[float], digits: int = 1) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), digits)


def _emotion_value(diary: Any, emotion: str) -> float:
    return float(getattr(diary, emotion, 0.0) or 0.0)


def _mind_temperature(diary: Any) -> float:
    """
    Project-internal trend score only.
    Revalidate after the final 8-emotion score distribution is fixed.
    """
    pos_avg = mean(_emotion_value(diary, e) for e in POSITIVE_EMOTIONS)
    neg_avg = mean(_emotion_value(diary, e) for e in NEGATIVE_EMOTIONS)
    return max(0.0, min(100.0, 50.0 + (pos_avg - neg_avg) / 2.0))


def _is_usable_diary(diary: Any) -> bool:
    status = getattr(diary, "analysis_status", None)
    return status in (None, "completed")


def _safe_mean(values: List[float]) -> Optional[float]:
    return mean(values) if values else None


def _safe_pstdev(values: List[float]) -> Optional[float]:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    return pstdev(values)


def _make_record(diary: Any) -> Dict[str, Any]:
    created_at = _as_utc(getattr(diary, "created_at", None))
    emotions = {e: _round(_emotion_value(diary, e)) for e in ALL_EMOTIONS}
    return {
        "diary_id": getattr(diary, "id", None),
        "created_at": created_at,
        "date": created_at.strftime("%Y-%m-%d") if created_at else None,
        "temperature": _round(_mind_temperature(diary)),
        "emotions": emotions,
    }


def _prepare_records(diaries: List[Any]) -> List[Dict[str, Any]]:
    records = [_make_record(d) for d in diaries if _is_usable_diary(d)]
    records = [r for r in records if r["created_at"] is not None]
    records.sort(key=lambda r: r["created_at"])

    prev_temp = None
    for record in records:
        current = float(record["temperature"])
        record["delta_from_prev"] = (
            None if prev_temp is None else _round(current - prev_temp)
        )
        prev_temp = current
    return records


def _build_baseline(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    status = "ready" if len(records) >= MIN_BASELINE_RECORDS else "building"

    temps = [float(r["temperature"]) for r in records]
    temp_mean = _safe_mean(temps)
    temp_std = _safe_pstdev(temps)

    if temp_mean is None:
        personal_range = None
    else:
        band = max(5.0, 2.0 * float(temp_std or 0.0))
        personal_range = {
            "lower": _round(max(0.0, temp_mean - band)),
            "upper": _round(min(100.0, temp_mean + band)),
        }

    emotion_stats = {}
    for emotion in ALL_EMOTIONS:
        values = [float(r["emotions"][emotion]) for r in records]
        emotion_stats[emotion] = {
            "mean": _round(_safe_mean(values)),
            "std": _round(_safe_pstdev(values)),
        }

    return {
        "status": status,
        "record_count": len(records),
        "temperature": {
            "mean": _round(temp_mean),
            "std": _round(temp_std),
            "personal_range": personal_range,
        },
        "emotions": emotion_stats,
    }


def _build_recent_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    temps = [float(r["temperature"]) for r in records]

    emotion_avg = {}
    for emotion in ALL_EMOTIONS:
        values = [float(r["emotions"][emotion]) for r in records]
        emotion_avg[emotion] = _round(_safe_mean(values))

    temp_change = None
    if len(temps) >= 2:
        temp_change = temps[-1] - temps[0]

    return {
        "record_count": len(records),
        "temperature_avg": _round(_safe_mean(temps)),
        "temperature_change": _round(temp_change),
        "emotion_avg": emotion_avg,
    }


def _build_deviation(
    baseline: Dict[str, Any],
    recent: Dict[str, Any],
) -> Dict[str, Any]:
    if baseline["status"] != "ready":
        return {
            "status": "building",
            "temperature": None,
            "emotions": {e: None for e in ALL_EMOTIONS},
        }

    recent_temp = recent.get("temperature_avg")
    base_temp = baseline["temperature"].get("mean")
    base_std = float(baseline["temperature"].get("std") or 0.0)

    if recent_temp is None or base_temp is None:
        temp_dev = None
    else:
        delta = float(recent_temp) - float(base_temp)
        temp_dev = {
            "delta": _round(delta),
            "z_score": _round(delta / base_std, 2) if base_std >= 1.0 else None,
        }

    emotion_dev = {}
    for emotion in ALL_EMOTIONS:
        recent_v = recent["emotion_avg"].get(emotion)
        base_v = baseline["emotions"][emotion].get("mean")
        std = float(baseline["emotions"][emotion].get("std") or 0.0)

        if recent_v is None or base_v is None:
            emotion_dev[emotion] = None
            continue

        delta = float(recent_v) - float(base_v)
        emotion_dev[emotion] = {
            "delta": _round(delta),
            "z_score": _round(delta / std, 2) if std >= 1.0 else None,
        }

    return {
        "status": "ready",
        "temperature": temp_dev,
        "emotions": emotion_dev,
    }


def _adaptive_drop_threshold(baseline: Dict[str, Any]) -> float:
    if baseline["status"] != "ready":
        return FALLBACK_SUDDEN_DROP
    std = float(baseline["temperature"].get("std") or 0.0)
    return max(12.0, 1.5 * std)


def _baseline_departure_threshold(baseline: Dict[str, Any]) -> float:
    if baseline["status"] != "ready":
        return MIN_BASELINE_DEPARTURE
    std = float(baseline["temperature"].get("std") or 0.0)
    return max(MIN_BASELINE_DEPARTURE, std)


def _detect_change_point(
    recent_records: List[Dict[str, Any]],
    baseline: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if baseline["status"] != "ready" or len(recent_records) < 2:
        return None

    base_mean = baseline["temperature"].get("mean")
    if base_mean is None:
        return None

    base_mean = float(base_mean)
    base_std = float(baseline["temperature"].get("std") or 0.0)
    departure = max(MIN_CHANGE_POINT_DROP, 2.0 * base_std)
    lower_boundary = base_mean - departure
    followup_boundary = base_mean - max(5.0, base_std)
    drop_threshold = _adaptive_drop_threshold(baseline)

    for i, record in enumerate(recent_records):
        current = float(record["temperature"])
        if current > lower_boundary:
            continue

        delta = record.get("delta_from_prev")
        large_drop = delta is not None and float(delta) <= -drop_threshold
        persisted = (
            i + 1 < len(recent_records)
            and float(recent_records[i + 1]["temperature"]) <= followup_boundary
        )

        if large_drop or persisted:
            return {
                "date": record["date"],
                "temperature": _round(current),
                "baseline_temperature": _round(base_mean),
                "deviation": _round(current - base_mean),
                "detection_reason": (
                    "sudden_drop" if large_drop else "persistent_baseline_departure"
                ),
            }

    return None


def _detect_red_zone_events(
    records: List[Dict[str, Any]],
    recent_start: datetime,
    baseline: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if len(records) < 2:
        return []

    events = []
    drop_threshold = _adaptive_drop_threshold(baseline)
    base_mean = baseline["temperature"].get("mean")
    departure_threshold = _baseline_departure_threshold(baseline)

    for i in range(1, len(records)):
        current = records[i]
        previous = records[i - 1]

        if current["created_at"] < recent_start:
            continue

        previous_temp = float(previous["temperature"])
        current_temp = float(current["temperature"])
        drop_amount = previous_temp - current_temp

        if drop_amount < drop_threshold:
            continue

        if baseline["status"] == "ready" and base_mean is not None:
            if current_temp > float(base_mean) - departure_threshold:
                continue

        events.append({
            "record_index": i,
            "date": current["date"],
            "previous_date": previous["date"],
            "previous_temperature": _round(previous_temp),
            "temperature": _round(current_temp),
            "drop_amount": _round(drop_amount),
            "threshold_used": _round(drop_threshold),
        })

    return events


def _calculate_recovery(
    records: List[Dict[str, Any]],
    red_events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    recovery_events = []

    for event in red_events:
        event_index = int(event["record_index"])
        current_temp = float(event["temperature"])
        drop_amount = float(event["drop_amount"])

        future = records[
            event_index + 1:
            event_index + 1 + RECOVERY_LOOKAHEAD_RECORDS
        ]

        if not future or drop_amount <= 0:
            recovery_events.append({
                "date": event["date"],
                "status": "pending",
                "best_recovery_ratio": None,
                "records_to_best_recovery": None,
                "recovered_50pct": False,
                "records_to_50pct": None,
            })
            continue

        best_ratio = 0.0
        best_steps = None
        first_50_steps = None

        for step, record in enumerate(future, start=1):
            rebound = float(record["temperature"]) - current_temp
            ratio = max(0.0, min(rebound / drop_amount, 1.0))

            if ratio > best_ratio:
                best_ratio = ratio
                best_steps = step

            if first_50_steps is None and ratio >= 0.5:
                first_50_steps = step

        recovery_events.append({
            "date": event["date"],
            "status": "evaluated",
            "best_recovery_ratio": _round(best_ratio * 100.0),
            "records_to_best_recovery": best_steps,
            "recovered_50pct": first_50_steps is not None,
            "records_to_50pct": first_50_steps,
        })

    evaluated = [e for e in recovery_events if e["status"] == "evaluated"]
    ratios = [
        float(e["best_recovery_ratio"])
        for e in evaluated
        if e["best_recovery_ratio"] is not None
    ]
    records_to_50 = [
        float(e["records_to_50pct"])
        for e in evaluated
        if e["records_to_50pct"] is not None
    ]

    return {
        "index": _round(_safe_mean(ratios)),
        "event_count": len(red_events),
        "evaluated_event_count": len(evaluated),
        "recovery_observed_count": sum(
            1 for e in evaluated if float(e["best_recovery_ratio"] or 0.0) > 0.0
        ),
        "recovered_50pct_count": sum(
            1 for e in evaluated if e["recovered_50pct"]
        ),
        "avg_records_to_50pct": _round(_safe_mean(records_to_50)),
        "events": recovery_events,
    }


def _public_trend_records(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return [{
        "diary_id": r["diary_id"],
        "date": r["date"],
        "temperature": r["temperature"],
        "delta_from_prev": r["delta_from_prev"],
        "emotions": r["emotions"],
    } for r in records]


def analyze_personal_emotion_trend(
    db: Session,
    user_id: str,
) -> Dict[str, Any]:
    """
    Part 2 analysis only:
    baseline, deviation, change point, red-zone events, recovery, recent trend.

    It intentionally does NOT decide LOW/MEDIUM/HIGH and does NOT handle
    PHQ, GPT, routines, Self-Report interpretation, or UI.
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=BASELINE_DAYS)
    recent_start = now - timedelta(days=RECENT_DAYS)

    diaries = (
        db.query(models.Diary)
        .filter(
            models.Diary.user_id == user_id,
            models.Diary.created_at >= since,
        )
        .order_by(models.Diary.created_at.asc())
        .all()
    )

    records = _prepare_records(diaries)

    if not records:
        return {
            "user_id": user_id,
            "generated_at": now.isoformat(),
            "data_status": "insufficient",
            "baseline_status": "building",
            "baseline_deviation": None,
            "change_point": None,
            "sudden_drop_count": 0,
            "recovery_index": None,
            "baseline": {
                "status": "building",
                "record_count": 0,
                "temperature": {
                    "mean": None,
                    "std": None,
                    "personal_range": None,
                },
                "emotions": {
                    e: {"mean": None, "std": None} for e in ALL_EMOTIONS
                },
            },
            "recent": {
                "record_count": 0,
                "temperature_avg": None,
                "temperature_change": None,
                "emotion_avg": {e: None for e in ALL_EMOTIONS},
            },
            "deviation": {
                "status": "building",
                "temperature": None,
                "emotions": {e: None for e in ALL_EMOTIONS},
            },
            "change_point_detail": None,
            "red_zone": {
                "count": 0,
                "method": "record_drop_plus_personal_baseline",
                "events": [],
            },
            "recovery": {
                "index": None,
                "event_count": 0,
                "evaluated_event_count": 0,
                "recovery_observed_count": 0,
                "recovered_50pct_count": 0,
                "avg_records_to_50pct": None,
                "events": [],
            },
            "trend": [],
        }

    baseline_records = [r for r in records if r["created_at"] < recent_start]
    recent_records = [r for r in records if r["created_at"] >= recent_start]

    baseline = _build_baseline(baseline_records)
    recent = _build_recent_summary(recent_records)
    deviation = _build_deviation(baseline, recent)
    change_point = _detect_change_point(recent_records, baseline)
    red_events = _detect_red_zone_events(records, recent_start, baseline)
    recovery = _calculate_recovery(records, red_events)

    data_status = (
        "sufficient"
        if baseline["status"] == "ready" and len(recent_records) >= MIN_RECENT_RECORDS
        else "building"
    )

    baseline_deviation = None
    if deviation["temperature"]:
        baseline_deviation = deviation["temperature"].get("delta")

    return {
        "user_id": user_id,
        "generated_at": now.isoformat(),
        "window": {
            "baseline_days": BASELINE_DAYS,
            "recent_days": RECENT_DAYS,
            "baseline_record_count": len(baseline_records),
            "recent_record_count": len(recent_records),
        },
        "data_status": data_status,

        # Shortcuts for Part 1 / Part 4 integration.
        "baseline_status": baseline["status"],
        "baseline_deviation": baseline_deviation,
        "change_point": change_point.get("date") if change_point else None,
        "sudden_drop_count": len(red_events),
        "recovery_index": recovery["index"],

        # Detailed Part 2 result.
        "baseline": baseline,
        "recent": recent,
        "deviation": deviation,
        "change_point_detail": change_point,
        "red_zone": {
            "count": len(red_events),
            "method": "record_drop_plus_personal_baseline",
            "events": [
                {k: v for k, v in event.items() if k != "record_index"}
                for event in red_events
            ],
        },
        "recovery": recovery,
        "trend": _public_trend_records(recent_records),
    }
