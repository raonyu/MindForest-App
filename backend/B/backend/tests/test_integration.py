"""Local merge regression tests: isolated SQLite; no real AI calls or production data."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

_tmp = tempfile.TemporaryDirectory(prefix="mindforest-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(_tmp.name) / "test.db").as_posix()
os.environ.pop("OPENAI_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main
import models
from database import engine, SessionLocal
from fastapi.testclient import TestClient
from routers.diary import run_emotion_analysis
from services.weekly_report import build_chat_report_summary
from routine_manager import ROUTINE_MASTER

EMOTIONS = dict(joy=80, trust=65, fear=10, surprise=15, sadness=5, disgust=5, anger=5, anticipation=60)
RESULT = dict(emotions=EMOTIONS, dominant_emotion="joy", bws_used=False, analysis_comment="test")


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        models.Base.metadata.drop_all(engine)
        models.Base.metadata.create_all(engine)
        self.client = TestClient(main.app)
        self.db = SessionLocal()
        self.addCleanup(self.db.close)
        self.addCleanup(self.client.close)
        self.db.add(models.User(id="tester", password="unused", is_onboarding_done=True, assigned_category="DEPRESSION"))
        self.db.add(models.Animal(category="DEPRESSION", name="turtle", emoji="T", description="test"))
        self.db.add(models.Survey(survey_type="DEPRESSION", question_num=1, question_text="test"))
        for category, levels in ROUTINE_MASTER.items():
            for level, texts in levels.items():
                for content in texts:
                    self.db.add(models.RoutineMaster(category=category, level=level, content=content))
        self.db.commit()

    def save(self, result=RESULT, **extra):
        with patch("routers.diary.analyze_emotion_pipeline", return_value=result):
            response = self.client.post("/api/diary", json=dict(user_id="tester", date="2026-10-25", main_text="test", emotion="sadness", emotion_intensity=4, **extra))
        self.assertEqual(response.status_code, 202, response.text)
        return response.json()["diary_id"]

    def test_auth(self):
        self.assertEqual(self.client.post("/api/user/signup", json={"id":"new","password":"testpass"}).status_code,200)
        self.assertEqual(self.client.post("/api/user/login", json={"id":"new","password":"testpass"}).status_code,200)
        self.assertEqual(self.client.post("/api/user/login", json={"id":"new","password":"bad"}).status_code,401)

    def test_onboarding_and_daily_routines(self):
        with patch("routers.user.get_chat_response", return_value={"category":"DEPRESSION"}):
            r=self.client.post("/api/user/onboarding",json={"user_id":"tester","responses":["test"]})
        self.assertEqual(r.status_code,200)
        self.assertEqual(self.db.query(models.UserRoutine).count(),3)
        self.assertEqual(len(self.client.get("/api/routines/today/tester").json()),3)

    def test_completed_analysis_keeps_self_report_separate(self):
        diary_id=self.save()
        status=self.client.get(f"/api/diary/{diary_id}/analysis-status").json()
        self.assertEqual(status["status"],"completed")
        diary=self.db.get(models.Diary,diary_id)
        self.assertEqual((diary.emotion,diary.emotion_intensity,diary.joy),("sadness",4,80))
        self.assertEqual(self.db.query(models.Analysis).one().emotion,"joy")
        self.assertEqual(self.client.get("/api/diary/monthly?user_id=tester&year=2026&month=10").json()["data"][0]["emotion_intensity"],4)

    def test_model_failure_preserves_diary_and_excludes_fake_scores(self):
        diary_id=self.save(result=None)
        status=self.client.get(f"/api/diary/{diary_id}/analysis-status").json()
        self.assertEqual(status["status"],"failed")
        self.assertTrue(status["message"])
        self.assertIn("test",self.db.get(models.Diary,diary_id).content)
        report=self.client.get("/api/analysis/api/report/tester").json()["weekly_report"]
        self.assertNotEqual(report["cards"]["spectrum"]["status"],"ready")

    def test_bws_and_delete_cleanup(self):
        result={**RESULT,"bws_used":True,"bws_validation":{"candidates":["joy","sadness"],"best_emotion":"joy","worst_emotion":"sadness","reasoning":"test"}}
        diary_id=self.save(result)
        self.assertEqual(self.db.query(models.BwsRecord).count(),1)
        self.assertEqual(self.client.delete("/api/diary?user_id=tester&date=2026-10-25").status_code,200)
        self.assertEqual(self.db.query(models.Analysis).count(),0)
        self.assertEqual(self.db.query(models.BwsRecord).count(),0)
        self.assertEqual(self.client.get(f"/api/diary/{diary_id}/analysis-status").status_code,404)

    def test_stale_analysis_cannot_overwrite_edit(self):
        diary_id=self.save()
        self.save(result={**RESULT,"emotions":{**EMOTIONS,"joy":60}})
        with patch("routers.diary.analyze_emotion_pipeline",return_value=RESULT):
            run_emotion_analysis(diary_id,1,"old text")
        self.db.expire_all()
        self.assertEqual(self.db.get(models.Diary,diary_id).joy,60)

    def test_invalid_input(self):
        for changes in ({"date":"bad"},{"emotion_intensity":8}):
            r=self.client.post("/api/diary",json={"user_id":"tester",**changes})
            self.assertEqual(r.status_code,422,r.text)
        self.assertEqual(self.client.post("/api/diary",json={"user_id":"missing"}).status_code,404)

    def test_self_report_without_text_does_not_invent_ai_scores(self):
        r=self.client.post("/api/diary",json={"user_id":"tester","emotion":"joy","emotion_intensity":3})
        self.assertEqual(r.status_code,202)
        diary_id=r.json()["diary_id"]
        self.assertEqual(self.client.get(f"/api/diary/{diary_id}/analysis-status").json()["status"],"skipped")
        self.assertEqual(self.db.query(models.Analysis).count(),0)

    def test_survey_requires_answers(self):
        body=dict(user_id="tester",survey_type="DEPRESSION",answers=[])
        self.assertEqual(self.client.post("/api/survey/submit",json=body).status_code,422)
        body["answers"]=[dict(question_num=1,answer=2)]
        self.assertEqual(self.client.post("/api/survey/submit",json=body).status_code,200)
        self.assertTrue(build_chat_report_summary(self.db,"tester"))

    def test_report_trend_and_chat_share_context(self):
        for i in range(22):
            self.db.add(models.Diary(user_id="tester",content="record",emotion="joy",analysis_status="completed",created_at=datetime.now(timezone.utc)-timedelta(days=i),**EMOTIONS))
        self.db.add(models.SurveyResult(user_id="tester",survey_type="DEPRESSION",score=2,result_message="test"))
        self.db.commit()
        report=self.client.get("/api/analysis/api/report/tester")
        self.assertEqual(report.status_code,200)
        self.assertEqual(report.json()["weekly_report"]["cards"]["spectrum"]["status"],"ready")
        self.assertEqual(self.client.get("/api/analysis/api/emotion-trend/tester").status_code,200)
        with patch("routers.chatbot.get_chat_response",return_value={"is_finished":False,"reply_message":"test"}) as ai:
            r=self.client.post("/api/chatbot/api/chat",json={"user_id":"tester","message":"test"})
            self.assertEqual(r.status_code,200)
            self.assertTrue(ai.call_args.kwargs["report_summary"])
        self.assertEqual(self.client.get("/api/chat-history/api/chat/history?user_id=tester").json()["total"],2)

    def test_schema_upgrade_is_repeatable(self):
        from migrate_report_fields import main as migrate
        migrate();migrate()
        self.assertEqual(self.db.query(models.User).count(),1)

    def test_upgrade_preserves_legacy_diary(self):
        from sqlalchemy import create_engine, text, inspect
        from migrate_report_fields import main as migrate
        legacy = create_engine("sqlite:///:memory:")
        try:
            with legacy.begin() as connection:
                connection.execute(text("CREATE TABLE diaries (id INTEGER PRIMARY KEY, user_id VARCHAR, content TEXT)"))
                connection.execute(text("INSERT INTO diaries VALUES (42, 'old-user', 'keep this diary')"))
            with patch("migrate_report_fields.engine", legacy):
                migrate(); migrate()
            columns = {column["name"] for column in inspect(legacy).get_columns("diaries")}
            self.assertIn("analysis_status", columns)
            self.assertIn("emotion_intensity", columns)
            with legacy.connect() as connection:
                row = connection.execute(text("SELECT content, analysis_status FROM diaries WHERE id=42")).one()
                self.assertEqual(tuple(row), ("keep this diary", "idle"))
        finally:
            legacy.dispose()


def tearDownModule():
    engine.dispose()
    _tmp.cleanup()


if __name__=="__main__":
    unittest.main()
