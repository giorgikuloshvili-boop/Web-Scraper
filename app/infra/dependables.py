from typing import Any, Dict, Generator
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from starlette.requests import Request

from app.core.config import settings

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_task_store: Dict[UUID, Dict[str, Any]] = {}
Base = declarative_base()

def get_task_store() -> Dict[UUID, Dict[str, Any]]:
    return _task_store


def get_core(request: Request) -> Any:
    return request.app.state.core


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()