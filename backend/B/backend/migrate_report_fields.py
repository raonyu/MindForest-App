"""주간 리포트용 스키마 추가 (1회 실행).

- diaries.keywords 컬럼 추가 (상황·키워드 카드용)
- bws_records 테이블 생성 (복합 감정 데이 카드용)

기존 테이블은 건드리지 않으며, 여러 번 실행해도 안전하다.

    python migrate_report_fields.py
"""

from sqlalchemy import text

import models
from database import engine


def main() -> None:
    # 새 테이블(bws_records)은 create_all이 알아서 만든다. 기존 테이블은 변경하지 않는다.
    models.Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE diaries ADD COLUMN IF NOT EXISTS keywords VARCHAR"))

    print("✅ 마이그레이션 완료: diaries.keywords, bws_records")


if __name__ == "__main__":
    main()
