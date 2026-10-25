"""Regression scenarios for report enhancement; no external AI or real user database."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import test_integration as support
from services.emotion_scores import temperature, EMOTIONS
from services.report_enhancements import routine_card, self_report_card, keyword_card
from services.weekly_report import EMOTION_LABELS, EMOTION_EMOJI
from services.situation_keywords import extract_topics
from services.routine_observations import set_completion, record_after_analysis
from services.emotion_pipeline import analyze_emotion_pipeline
from benchmark_emotions import classification_metrics

models = support.models


class EnhancementTests(unittest.TestCase):
    setUp = support.IntegrationTests.setUp

    def diary(self, days=0, **changes):
        values = dict(user_id="tester", content="시험 때문에 잠을 못 자고 친구와 팀플을 했다.", emotion="sadness", emotion_intensity=4,
                      analysis_status="completed", analysis_version=1, created_at=datetime.now(timezone.utc)-timedelta(days=days), **support.EMOTIONS)
        values.update(changes)
        row=models.Diary(**values);self.db.add(row);self.db.commit();return row

    def routine(self, day=None, completed=False, content=None):
        master=self.db.query(models.RoutineMaster).filter(models.RoutineMaster.content==content).first() if content else self.db.query(models.RoutineMaster).first()
        row=models.UserRoutine(user_id="tester",routine_id=master.id,date=day or datetime.now(timezone.utc).date(),is_completed=completed)
        self.db.add(row);self.db.commit();return row

    def test_temperature_is_shared_and_surprise_is_neutral(self):
        from services.weekly_report import _temperature
        from services.emotion_trend_logic import _mind_temperature
        from services.user_state_logic import _mind_temperature as chat_temperature
        row=self.diary(surprise=0)
        expected=temperature(row)
        row.surprise=100
        for calculate in (temperature,_temperature,_mind_temperature,chat_temperature):
            self.assertAlmostEqual(calculate(row),expected)

    def test_self_report_comparison_preserves_distinct_scales(self):
        row=self.diary()
        data=self_report_card([row])["data"]
        choice=data["items"][0]["choices"][0]
        self.assertEqual((choice["intensity"],choice["ai_score"]),(4,5))
        self.assertEqual(data["items"][0]["self_temperature"],10)
        self.assertGreater(data["items"][0]["gap"],0)
        self.assertFalse(data["items"][0]["dominant_matches"])

    def test_no_self_report_does_not_make_a_comparison(self):
        self.assertIsNone(self_report_card([self.diary(emotion_intensity=None)])["data"])

    def test_keywords_are_extracted_on_save(self):
        with patch("routers.diary.analyze_emotion_pipeline",return_value=support.RESULT):
            r=self.client.post("/api/diary",json={"user_id":"tester","main_text":"시험과 팀플 때문에 밤샘했다. 친구와 가족에게 취업 이야기를 했다."})
        self.assertEqual(r.status_code,202)
        row=self.db.get(models.Diary,r.json()["diary_id"])
        self.assertTrue({"시험","팀플","수면","친구","가족","취업"}.issubset(set(row.keywords.split(","))))

    def test_legacy_text_keywords_work_without_backfill(self):
        rows=[self.diary(i,content=json.dumps({"mainText":"시험 때문에 잠을 못 잤다."})) for i in range(3)]
        result=keyword_card(rows,EMOTION_LABELS,EMOTION_EMOJI)
        self.assertEqual(result["status"],"ready")
        self.assertEqual({item["keyword"] for item in result["data"]["items"]},{"시험","수면"})
        self.assertEqual(extract_topics("아무 관련 표현 없음"),[])

    def test_uncompleted_named_routine_is_not_counted(self):
        row=self.diary(routine_name="not actually done",is_done=False,score_diff=10)
        result=routine_card(self.db,"tester",[row])
        self.assertEqual(result["data"]["items"],[])

    def test_completion_never_awards_ten_points_and_undo_cleans_snapshot(self):
        row=self.diary(analysis_completed_at=datetime.now(timezone.utc)-timedelta(minutes=5))
        routine=self.routine()
        r=self.client.patch(f"/api/routines/complete/{routine.id}",json={"is_completed":True})
        self.assertEqual(r.status_code,200)
        self.db.expire_all()
        self.assertIsNone(row.score_diff)
        self.assertEqual(self.db.query(models.RoutineObservation).count(),1)
        self.client.patch(f"/api/routines/complete/{routine.id}",json={"is_completed":False})
        self.db.expire_all()
        self.assertFalse(row.is_done)
        self.assertEqual(self.db.query(models.RoutineObservation).count(),0)

    def test_observed_before_after_can_be_negative(self):
        now=datetime.now(timezone.utc)
        row=self.diary(analysis_requested_at=now-timedelta(minutes=10),analysis_completed_at=now-timedelta(minutes=9))
        routine=self.routine()
        before=temperature(row)
        set_completion(self.db,routine,True,now=now-timedelta(minutes=5));self.db.commit()
        row.analysis_requested_at=now-timedelta(minutes=1)
        row.analysis_version=2
        for emotion in EMOTIONS:setattr(row,emotion,20 if emotion in ("joy","trust","anticipation") else 80)
        row.analysis_completed_at=now
        record_after_analysis(self.db,row);self.db.commit()
        observation=self.db.query(models.RoutineObservation).one()
        self.assertAlmostEqual(observation.before_temperature,before)
        self.assertLess(observation.after_temperature-observation.before_temperature,0)
        result=routine_card(self.db,"tester",[row])["data"]["paired_items"][0]
        self.assertLess(result["signed_delta"],0)
        self.assertFalse(result["enough"])

    def test_missing_before_data_does_not_invent_effect(self):
        now=datetime.now(timezone.utc)
        routine=self.routine()
        set_completion(self.db,routine,True,now=now-timedelta(minutes=5));self.db.commit()
        row=self.diary(analysis_requested_at=now,analysis_completed_at=now)
        record_after_analysis(self.db,row);self.db.commit()
        self.assertIsNone(self.db.query(models.RoutineObservation).one().after_temperature)
        self.assertEqual(routine_card(self.db,"tester",[row])["data"]["paired_items"],[])

    def test_text_submitted_before_completion_is_not_post_measurement(self):
        now=datetime.now(timezone.utc)
        row=self.diary(analysis_requested_at=now-timedelta(minutes=10),analysis_completed_at=now-timedelta(minutes=9))
        routine=self.routine();set_completion(self.db,routine,True,now=now-timedelta(minutes=5));self.db.commit()
        row.analysis_completed_at=now
        record_after_analysis(self.db,row);self.db.commit()
        self.assertIsNone(self.db.query(models.RoutineObservation).one().after_temperature)

    def test_between_day_rank_requires_completed_and_enough_records(self):
        rows=[]
        for day in range(3):
            row=self.diary(day);rows.append(row);self.routine(row.created_at.date(),completed=True)
        for day in range(3,6):
            rows.append(self.diary(day,joy=5,trust=5,anticipation=5,sadness=80,anger=80,fear=80,disgust=80))
        result=routine_card(self.db,"tester",rows)
        self.assertEqual(result["status"],"ready")
        self.assertEqual(result["data"]["items"][0]["rank"],1)
        self.assertEqual(result["data"]["baseline_days"],3)
        self.assertGreater(result["data"]["items"][0]["signed_delta"],0)

    def test_pipeline_instrumentation_does_not_change_scores(self):
        emotions={e:10 for e in EMOTIONS};emotions.update(joy=70,sadness=68)
        with patch("services.emotion_pipeline.predict_emotions",return_value=emotions),patch("services.emotion_pipeline.run_bws_llm",return_value={"best_emotion":"sadness","worst_emotion":"joy","reasoning":"test"}):
            result=analyze_emotion_pipeline("test")
        self.assertEqual(result["emotions"],emotions)
        self.assertEqual(result["dominant_emotion"],"sadness")
        self.assertTrue(result["metrics"]["bws_attempted"])
        self.assertGreaterEqual(result["metrics"]["total_ms"],0)

    def test_invalid_bws_is_not_counted_as_verified(self):
        from types import SimpleNamespace
        from services.bws_logic import run_bws_llm
        response=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"best_emotion":"unknown","worst_emotion":"unknown"}'))])
        with patch("services.bws_logic._get_client") as client:
            client.return_value.chat.completions.create.return_value=response
            self.assertIsNone(run_bws_llm("test",{"joy":70,"sadness":68}))

    def test_discarded_runs_do_not_change_latency_denominator(self):
        from services.analysis_metrics import persist_run, summary
        row=self.diary(analysis_version=2)
        persist_run(support.SessionLocal,row.id,1,"failed",{"total_ms":999,"bws_attempted":True})
        data=summary(self.db,"tester")
        self.assertEqual(data["attempts"],0)
        self.assertIsNone(data["bws_call_rate"])

    def test_client_cannot_claim_routine_effect_in_diary_payload(self):
        with patch("routers.diary.analyze_emotion_pipeline",return_value=support.RESULT):
            r=self.client.post("/api/diary",json={"user_id":"tester","main_text":"test","routine_name":"fake","is_done":True,"score_diff":999})
        self.db.expire_all()
        row=self.db.get(models.Diary,r.json()["diary_id"])
        self.assertFalse(row.is_done)
        self.assertIsNone(row.score_diff)

    def test_undo_one_routine_keeps_another_completed(self):
        row=self.diary()
        first=self.routine()
        second_master=self.db.query(models.RoutineMaster).filter(models.RoutineMaster.id != first.routine_id).first()
        second=self.routine(content=second_master.content)
        set_completion(self.db,first,True);set_completion(self.db,second,True);self.db.commit()
        set_completion(self.db,first,False);self.db.commit()
        self.db.refresh(row)
        self.assertTrue(row.is_done)
        self.assertEqual(row.routine_name,second_master.content)

    def test_runtime_metrics_are_persisted_per_user(self):
        result={**support.RESULT,"metrics":{"total_ms":123,"model_ms":100,"bws_ms":23,"bws_attempted":True,"bws_used":True}}
        with patch("routers.diary.analyze_emotion_pipeline",return_value=result):
            self.client.post("/api/diary",json={"user_id":"tester","main_text":"test"})
        data=self.client.get("/api/analysis/api/metrics/tester").json()
        self.assertEqual(data["average_analysis_ms"],123)
        self.assertEqual(data["bws_call_rate"],1)
        self.assertEqual(data["attempts"],1)
        self.assertEqual(self.client.get("/api/analysis/api/metrics/tester?days=999").status_code,422)

    def test_recorded_prediction_evaluation_and_baseline_needs_no_model(self):
        labels={e:int(e=="joy") for e in EMOTIONS};prediction={e:100*labels[e] for e in EMOTIONS}
        result=classification_metrics([labels],[prediction]);self.assertEqual(result["micro_f1"],1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            (tmp/"labels.jsonl").write_text(json.dumps({"id":"one","text":"test","labels":labels})+"\n")
            (tmp/"predictions.jsonl").write_text(json.dumps({"id":"one","emotions":prediction})+"\n")
            script=Path(__file__).resolve().parents[1]/"benchmark_emotions.py"
            command=[sys.executable,str(script),"--dataset",str(tmp/"labels.jsonl"),"--predictions",str(tmp/"predictions.jsonl"),"--gpt-predictions",str(tmp/"predictions.jsonl"),"--output",str(tmp/"report.json")]
            completed=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            report=json.loads((tmp/"report.json").read_text())
            self.assertEqual(report["gpt_direct_baseline"]["micro_f1"],1)
            self.assertIsNone(report["runtime"]["average_analysis_ms"])

    def test_report_contains_comparison_and_topics(self):
        self.diary()
        report=self.client.get("/api/analysis/api/report/tester").json()["weekly_report"]
        self.assertIn("self_report",report["cards"])
        self.assertIsNotNone(report["cards"]["self_report"]["data"])
        self.assertIsNotNone(report["cards"]["keywords"]["data"])
