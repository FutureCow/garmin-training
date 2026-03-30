from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    fernet_key: str
    anthropic_api_key: str
    garmin_tokens_dir: str = "/opt/garmin-training/garmin-tokens"

    class Config:
        env_file = ".env"


settings = Settings()
