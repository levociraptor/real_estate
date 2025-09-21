from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MAX_IMG_SIZE: int
    ALLOWED_CONTENT_TYPES: list[str]

    # Postgres
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    # Pool settings for postgres
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10

    RABBIT_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    QUEUE_NAME: str = "images"

    PATH_TO_IMAGE: str = "uploaded_images"

    THUMBNAILS_RESOLUTION: list[int]

    @field_validator('MAX_IMG_SIZE', mode='before')
    @classmethod
    def convert_mb_to_bytes(cls, v):
        """Преобразует МБ в байты"""
        if isinstance(v, str):
            v = int(v)
        return v * 1024 * 1024

    @property
    def database_url(self):
        user = self.POSTGRES_USER
        password = self.POSTGRES_PASSWORD
        host = self.POSTGRES_HOST
        port = self.POSTGRES_PORT
        db = self.POSTGRES_DB
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
