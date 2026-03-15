from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://Mind:1234@localhost:5432/Table"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
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