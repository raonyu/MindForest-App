from database import engine
from sqlalchemy import text

try:
    # database.py의 engine을 가져와서 DB에 직접 명령을 내립니다.
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE diaries ADD COLUMN keywords TEXT;"))
        print("성공: diaries 테이블에 keywords 컬럼이 추가되었습니다")
except Exception as e:
    print("⚠️ 에러 (또는 이미 추가됨):", e)