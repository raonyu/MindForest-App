from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import mean
import models
from services.emotion_scores import EMOTIONS, temperature, self_report_temperature, score, usable
from services.situation_keywords import extract_topics, diary_text

MIN_RECORDS = 3


def card(status, data=None, message=None):
    return {"status": status, "data": data, "message": message}


def self_report_card(diaries):
    items = []
    for diary in reversed(diaries):
        own = self_report_temperature(diary)
        if own is None or not usable(diary):
            continue
        choices = []
        for emotion, intensity in [(diary.emotion, diary.emotion_intensity), (diary.secondary_emotion, diary.secondary_emotion_intensity)]:
            if emotion in EMOTIONS and intensity is not None:
                choices.append({"emotion": emotion, "intensity": intensity, "ai_score": score(diary, emotion)})
        dominant = diary.analysis_data.emotion if diary.analysis_data else max(EMOTIONS, key=lambda e: score(diary, e))
        items.append({
            "date": diary.created_at.date().isoformat(), "choices": choices,
            "ai_dominant": dominant, "dominant_matches": dominant in [c["emotion"] for c in choices],
            "self_temperature": own, "ai_temperature": round(temperature(diary), 1),
            "gap": round(temperature(diary) - own, 1),
        })
    if not items:
        return card("insufficient", message="감정·강도를 직접 입력하고 AI 분석이 완료되면 함께 비교해드려요.")
    return card("ready" if len(items) >= MIN_RECORDS else "building", {
        "items": items, "records": len(items),
        "mean_absolute_gap": round(mean(abs(i["gap"]) for i in items), 1),
        "note": "자가보고 강도(1~5)와 AI 상대점수(0~100)는 서로 다른 척도예요. 마음 온도 차이는 서비스 내부 환산값이며, 어느 쪽이 정답이라는 뜻은 아니에요.",
    }, "기록이 더 쌓이면 반복되는 차이를 살펴볼 수 있어요." if len(items) < MIN_RECORDS else None)


def keyword_card(diaries, labels, emojis):
    pairs = Counter()
    totals = Counter()
    tagged = 0
    for diary in diaries:
        topics = set(extract_topics(diary_text(diary.content))) | {t.strip() for t in (diary.keywords or "").split(",") if t.strip()}
        if not topics:
            continue
        tagged += 1
        dominant = max(EMOTIONS, key=lambda e: score(diary, e))
        for topic in topics:
            totals[topic] += 1
            pairs[topic, dominant] += 1
    if not tagged:
        return card("insufficient", message="시험·수면·친구 등 반복되는 상황이 기록되면 감정과 함께 보여드려요.")
    items = [{"keyword": topic, "emotion": emotion, "label": labels[emotion], "emoji": emojis[emotion], "count": count, "keyword_count": totals[topic]} for (topic, emotion), count in sorted(pairs.items(), key=lambda row: (-row[1], row[0]))[:5]]
    return card("ready" if tagged >= MIN_RECORDS else "building", {
        "items": items, "records": tagged, "method": "topic_dictionary_v1",
        "note": "일기에서 정해진 주제 표현을 찾아 함께 나타난 감정을 집계했어요. 모든 상황을 인식하거나 원인을 판단하는 분석은 아니에요.",
    }, "상황 기록을 조금 더 모으고 있어요." if tagged < MIN_RECORDS else None)


def routine_card(db, user_id, diaries):
    if not diaries:
        return card("insufficient", message="분석이 완료된 감정 기록이 쌓이면 루틴과 함께 살펴볼 수 있어요.")
    days = sorted({d.created_at.date() for d in diaries})
    routines = db.query(models.UserRoutine).filter(models.UserRoutine.user_id == user_id, models.UserRoutine.date >= days[0], models.UserRoutine.date <= days[-1], models.UserRoutine.is_completed.is_(True)).all()
    done = defaultdict(set)
    names = {}
    for routine in routines:
        if routine.routine_detail:
            done[routine.date].add(routine.routine_detail.content)
            names[routine.id] = routine.routine_detail.content
    by_day = defaultdict(list)
    for diary in diaries:
        by_day[diary.created_at.date()].append(temperature(diary))
        # Historical clients may only have persisted Diary.is_done. Never infer from name alone.
        if diary.is_done and diary.routine_name:
            done[diary.created_at.date()].add(diary.routine_name)
    groups = defaultdict(list)
    baseline = []
    for day, scores in by_day.items():
        value = mean(scores)
        if not done[day]:
            baseline.append(value)
        for name in done[day]:
            groups[name].append(value)
    base = mean(baseline) if baseline else None
    items = []
    for name, values in groups.items():
        delta = mean(values) - base if base is not None else None
        enough = len(values) >= MIN_RECORDS and len(baseline) >= MIN_RECORDS
        items.append({"routine": name, "average": round(mean(values), 1), "delta": round(abs(delta), 1) if delta is not None else None,
                      "signed_delta": round(delta, 1) if delta is not None else None,
                      "direction": "up" if delta is not None and delta > .05 else "down" if delta is not None and delta < -.05 else "flat",
                      "records": len(values), "enough": enough})
    items.sort(key=lambda i: (not i["enough"], -(i["signed_delta"] if i["signed_delta"] is not None else -1000), i["routine"]))
    for rank, item in enumerate((i for i in items if i["enough"]), start=1):
        item["rank"] = rank

    observations = db.query(models.RoutineObservation).join(models.UserRoutine, models.UserRoutine.id == models.RoutineObservation.user_routine_id).filter(
        models.RoutineObservation.user_id == user_id, models.UserRoutine.is_completed.is_(True),
        models.UserRoutine.date >= days[0], models.UserRoutine.date <= days[-1],
    ).all()
    after_ids = {o.after_diary_id for o in observations if o.after_diary_id is not None}
    after_rows = {d.id: d for d in db.query(models.Diary).filter(models.Diary.id.in_(after_ids)).all()} if after_ids else {}
    valid = [o for o in observations if o.before_temperature is not None and o.after_temperature is not None and o.after_diary_id in after_rows
             and after_rows[o.after_diary_id].analysis_status == "completed" and after_rows[o.after_diary_id].analysis_version == o.after_version]
    shared = Counter((o.after_diary_id, o.after_version) for o in valid)
    paired = defaultdict(list)
    for observation in valid:
        name = names.get(observation.user_routine_id)
        if name:
            paired[name].append(observation)
    paired_items = []
    for name, rows in paired.items():
        delta = mean(o.after_temperature-o.before_temperature for o in rows)
        paired_items.append({"routine": name, "before_average": round(mean(o.before_temperature for o in rows),1),
            "after_average": round(mean(o.after_temperature for o in rows),1), "signed_delta": round(delta,1), "records":len(rows),
            "shared_records":sum(shared[o.after_diary_id,o.after_version] > 1 for o in rows), "enough":len(rows)>=MIN_RECORDS})
    paired_items.sort(key=lambda i:(not i["enough"],-i["signed_delta"],i["routine"]))
    status = "ready" if any(i["enough"] for i in items+paired_items) else "building" if items or observations else "insufficient"
    return card(status, {"items":items,"paired_items":paired_items,"baseline_average":round(base,1) if base is not None else None,"baseline_days":len(baseline),
        "paired_records":len(valid),"pending_records":len(observations)-len(valid),
        "note":"완료한 날의 평균 차이와 완료 전후 24시간 안의 관찰 기록을 구분했어요. 같은 루틴을 3회 이상 관찰한 뒤 순위를 표시해요. 다른 루틴·생활 요인이 함께 작용할 수 있어 인과 효과를 뜻하지 않아요."},
        "루틴 완료와 감정 기록이 더 쌓이면 비교가 가능해요." if status!="ready" else None)
