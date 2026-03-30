from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    fernet_key: str
    anthropic_api_key: str
    garmin_home_dir: str = "/opt/garmin-training/garmin-home"
    garmin_mcp_path: str = "/opt/garmin-connect-mcp/dist/index.js"
    playwright_browsers_path: str = "/opt/playwright"

    class Config:
        env_file = ".env"


settings = Settings()
