from collections.abc import Generator

from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy import create_engine

from app.core.config import settings


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {settings.db_schema}'))


def ensure_status_column() -> None:
    with engine.begin() as conn:
        conn.execute(text(f"""
            ALTER TABLE {settings.db_schema}.wnioski
            ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'nowy'
        """))
