from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Lynceus"
    APP_VERSION: str = "1.0.0"

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    JWT_SECRET_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()