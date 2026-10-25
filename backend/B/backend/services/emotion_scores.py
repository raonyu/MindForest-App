"""Shared service-internal scores. These are not diagnostic or calibrated intensity scales."""
import math
from statistics import mean

POSITIVE = ("joy", "trust", "anticipation")
NEGATIVE = ("sadness", "anger", "fear", "disgust")
NEUTRAL = ("surprise",)
EMOTIONS = POSITIVE + NEGATIVE + NEUTRAL


def score(record, emotion):
    raw = record.get(emotion, 0) if hasattr(record, "get") else getattr(record, emotion, 0)
    value = float(raw or 0)
    return min(100.0, max(0.0, value)) if math.isfinite(value) else 0.0


def temperature(record):
    return max(0.0, min(100.0, 50 + (mean(score(record, e) for e in POSITIVE) - mean(score(record, e) for e in NEGATIVE)) / 2))


def usable(record):
    status = getattr(record, "analysis_status", None)
    return status == "completed" or (status in (None, "idle") and any(score(record, e) for e in EMOTIONS))


def self_report_temperature(record):
    def get(key):
        return record.get(key) if hasattr(record, "get") else getattr(record, key, None)
    values = []
    for emotion, intensity in [(get("emotion"), get("emotion_intensity")), (get("secondary_emotion"), get("secondary_emotion_intensity"))]:
        if emotion not in EMOTIONS or intensity is None:
            continue
        strength = float(intensity)
        if not math.isfinite(strength) or not 1 <= strength <= 5:
            continue
        sign = 1 if emotion in POSITIVE else -1 if emotion in NEGATIVE else 0
        values.append(50 + sign * strength * 10)
    return round(mean(values), 1) if values else None
