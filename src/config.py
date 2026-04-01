from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    slack_channel_name: str = "ai-digest"

    # Gemini
    gemini_api_key: str

    # Tavily
    tavily_api_key: str

    # Notion
    notion_api_key: str
    notion_database_id: str

    # Scheduler
    schedule_interval_hours: int = Field(default=12, ge=1, le=24)

    # Limits
    max_items_per_digest: int = Field(default=20, ge=1, le=20)
    max_summary_chars: int = Field(default=500, ge=100, le=1000)

    # Server
    port: int = Field(default=8000, ge=1024, le=65535)


settings = Settings()
