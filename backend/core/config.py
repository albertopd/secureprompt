import secrets
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",  # Use top level .env file (one level above ./backend/)
        env_file_encoding="utf-8",
    )

    PROJECT_NAME: str = "SecurePrompt"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    API_V1_STR: str = "/api/v1"

    # Auth
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Mongo
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "secureprompt"
    MONGO_USERS_COLLECTION: str = "users"
    MONGO_AUDITS_COLLECTION: str = "audits"

    # Paths
    EMPLOYEES_CSV_PATH: str = "data/mock_employees.csv"


settings = Settings()