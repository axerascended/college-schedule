from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "sqlite:///./schedule.db"
    debug: bool = True
    college_name: str = "Валуйский колледж"


settings = Settings()
