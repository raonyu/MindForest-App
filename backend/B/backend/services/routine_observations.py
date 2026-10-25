"""Observed pre/post snapshots, not an assumed benefit for completing a routine."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, or_
import models
from services.emotion_scores import temperature

WINDOW = timedelta(hours=24)


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def set_completion(db, routine, completed, now=None):
    now = now or datetime.now(timezone.utc)
    changed = bool(routine.is_completed) != bool(completed)
    routine.is_completed = completed
    if changed:
        db.query(models.RoutineObservation).filter(models.RoutineObservation.user_routine_id == routine.id).delete(synchronize_session=False)
        routine.completed_at = now if completed else None
        if completed:
            before = db.query(models.Diary).filter(
                models.Diary.user_id == routine.user_id,
                models.Diary.analysis_status == "completed",
                models.Diary.analysis_completed_at <= now,
                models.Diary.analysis_completed_at >= now - WINDOW,
                func.date(models.Diary.created_at) == routine.date,
            ).order_by(models.Diary.analysis_completed_at.desc(), models.Diary.id.desc()).first()
            db.add(models.RoutineObservation(
                user_routine_id=routine.id, user_id=routine.user_id,
                completed_at=now,
                before_diary_id=before.id if before else None,
                before_version=before.analysis_version if before else None,
                before_temperature=temperature(before) if before else None,
            ))
    db.flush()
    # Compatibility fields reflect real completion, never a fabricated +10.
    completed_rows = db.query(models.UserRoutine).filter(
        models.UserRoutine.user_id == routine.user_id,
        models.UserRoutine.date == routine.date,
        models.UserRoutine.is_completed.is_(True),
    ).all()
    for diary in db.query(models.Diary).filter(
        models.Diary.user_id == routine.user_id, func.date(models.Diary.created_at) == routine.date,
    ):
        diary.is_done = bool(completed_rows)
        first = completed_rows[0].routine_detail if completed_rows else None
        diary.routine_name = first.content if first else None
        diary.routine_category = first.category if first else None
        diary.score_diff = None


def record_after_analysis(db, diary):
    if not diary.analysis_requested_at:
        return
    requested = aware(diary.analysis_requested_at)
    observations = db.query(models.RoutineObservation).join(
        models.UserRoutine, models.UserRoutine.id == models.RoutineObservation.user_routine_id,
    ).filter(
        models.RoutineObservation.user_id == diary.user_id,
        models.UserRoutine.is_completed.is_(True),
        models.UserRoutine.date == diary.created_at.date(),
        or_(models.RoutineObservation.after_diary_id.is_(None), models.RoutineObservation.after_diary_id == diary.id),
        models.RoutineObservation.before_temperature.is_not(None),
    ).all()
    for observation in observations:
        completed = aware(observation.completed_at)
        if completed < requested <= completed + WINDOW:
            observation.after_diary_id = diary.id
            observation.after_version = diary.analysis_version
            observation.after_temperature = temperature(diary)
            observation.measured_at = datetime.now(timezone.utc)
            diary.score_diff = round(observation.after_temperature - observation.before_temperature, 1)
