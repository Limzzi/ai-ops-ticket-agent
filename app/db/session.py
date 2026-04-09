from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def build_connect_args() -> dict:
    """
    현재 데이터베이스 종류에 맞는 connect_args를 반환한다.

    Returns:
        dict: SQLAlchemy 엔진 생성 시 사용할 추가 연결 옵션
    """
    if settings.is_sqlite:
        return {"check_same_thread": False}

    return {}


engine = create_engine(
    settings.database_url,
    connect_args=build_connect_args()
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)


def get_db():
    """
    데이터베이스 세션을 생성하고 요청 종료 후 정리한다.

    Yields:
        Session: SQLAlchemy 세션 객체
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()