from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    애플리케이션 전역 설정값을 관리한다.

    Attributes:
        openai_api_key (str): OpenAI API 인증 키
        app_name (str): 애플리케이션 이름
        app_version (str): 애플리케이션 버전
        debug (bool): 디버그 모드 여부
        database_url (str): 데이터베이스 연결 URL
    """

    openai_api_key: str
    app_name: str = "AI Ops Ticket Agent"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str = "sqlite:///./ai_ops_ticket_agent.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_sqlite(self) -> bool:
        """
        현재 database_url이 SQLite인지 여부를 반환한다.

        Returns:
            bool: SQLite 사용 여부
        """
        return self.database_url.startswith("sqlite")

    @property
    def is_postgresql(self) -> bool:
        """
        현재 database_url이 PostgreSQL인지 여부를 반환한다.

        Returns:
            bool: PostgreSQL 사용 여부
        """
        return self.database_url.startswith("postgresql")


settings = Settings()