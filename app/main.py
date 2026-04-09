from fastapi import FastAPI

from app.api.tickets import router as tickets_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


def create_app() -> FastAPI:
    """
    FastAPI 애플리케이션 객체를 생성하고 초기 설정을 적용한다.

    Returns:
        FastAPI: 설정이 완료된 애플리케이션 객체
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="실무형 AI 티켓 처리 에이전트 API"
    )

    Base.metadata.create_all(bind=engine)
    app.include_router(tickets_router)

    @app.get("/")
    def read_root() -> dict:
        """
        애플리케이션 루트 상태를 반환한다.

        Returns:
            dict: 애플리케이션 이름, 버전, 실행 상태 정보
        """
        return {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "status": "running"
        }

    @app.get("/health")
    def health_check() -> dict:
        """
        서버 상태를 확인하기 위한 헬스 체크 결과를 반환한다.

        Returns:
            dict: 서버 상태 정보
        """
        return {"status": "ok"}

    return app


app = create_app()