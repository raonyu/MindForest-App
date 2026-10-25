"""Add the merged diary fields without dropping existing data. Run explicitly before server startup."""
from sqlalchemy import inspect, text
import models
from database import engine


def main():
    models.Base.metadata.create_all(bind=engine)
    existing = {c["name"] for c in inspect(engine).get_columns("diaries")}
    columns = {
        "keywords": "VARCHAR", "emotion_intensity": "INTEGER",
        "secondary_emotion": "VARCHAR", "secondary_emotion_intensity": "INTEGER",
        "analysis_status": "VARCHAR NOT NULL DEFAULT 'idle'",
        "analysis_version": "INTEGER NOT NULL DEFAULT 0",
        "confidence": "FLOAT", "bws_used": "BOOLEAN NOT NULL DEFAULT FALSE",
        "analysis_completed_at": "TIMESTAMP", "analysis_error": "VARCHAR",
        "analysis_requested_at": "TIMESTAMP",
    }
    with engine.begin() as conn:
        for name, kind in columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE diaries ADD COLUMN {name} {kind}"))
        routine_columns = {c["name"] for c in inspect(conn).get_columns("user_routines")}
        if "completed_at" not in routine_columns:
            conn.execute(text("ALTER TABLE user_routines ADD COLUMN completed_at TIMESTAMP"))
    print("Diary schema ready (existing records preserved).")


if __name__ == "__main__":
    main()
