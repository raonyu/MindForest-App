import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 기본값은 팀 공용 개발 DB. 로컬 테스트 시 DATABASE_URL 환경변수로 바꿀 수 있다.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://Mind:1234@localhost:5432/Table")

# SQLite로 띄울 때만 필요한 옵션 (FastAPI는 요청마다 다른 스레드를 쓸 수 있다)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# FastAPI DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()