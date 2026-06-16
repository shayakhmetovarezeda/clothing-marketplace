from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int = 5433
    postgres_host: str = "localhost"

    jwt_secret: str = "dev_secret"
    jwt_expire_minutes: int = 60

    redis_url: str = "redis://localhost:6379/0"

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
