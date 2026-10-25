"""Operational measurements only; never store diary text or claim accuracy without labels."""
from datetime import datetime, timedelta, timezone
from math import ceil
from statistics import mean
import models


def persist_run(db_factory, diary_id, version, status, metrics):
    db = db_factory()
    try:
        diary = db.get(models.Diary, diary_id)
        if diary is None:
            return
        if diary.analysis_version != version:
            status = "discarded"
        db.add(models.AnalysisRun(
            user_id=diary.user_id, diary_id=diary_id, analysis_version=version, status=status,
            total_ms=max(0, float(metrics.get("total_ms", 0))), model_ms=metrics.get("model_ms"), bws_ms=metrics.get("bws_ms"),
            bws_attempted=bool(metrics.get("bws_attempted")), bws_used=bool(metrics.get("bws_used")),
        ))
        db.commit()
    except Exception:
        db.rollback()
        # Telemetry failure must not undo a saved diary or a successful analysis.
    finally:
        db.close()


def summary(db, user_id, days=30):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.query(models.AnalysisRun).filter(models.AnalysisRun.user_id == user_id, models.AnalysisRun.created_at >= since).all()
    measured = [r for r in rows if r.status in ("completed", "failed")]
    times = sorted(r.total_ms for r in measured)
    attempts = sum(bool(r.bws_attempted) for r in measured)
    return {
        "days": days, "attempts": len(measured), "completed": sum(r.status=="completed" for r in measured),
        "failed": sum(r.status=="failed" for r in measured), "skipped":sum(r.status=="skipped" for r in rows),
        "bws_attempts":attempts, "bws_successes":sum(bool(r.bws_used) for r in measured),
        "bws_call_rate":round(attempts/len(measured),4) if measured else None,
        "average_analysis_ms":round(mean(times),2) if times else None,
        "p95_analysis_ms":round(times[max(0,ceil(len(times)*.95)-1)],2) if times else None,
        "note":"모델·BWS 처리 시간이며 HTTP 왕복/저장 대기 시간이나 정확도를 나타내지 않습니다. 빈 텍스트·폐기된 이전 버전은 호출 비율 분모에서 제외합니다.",
    }
