from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_prefix="PHISIM_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
