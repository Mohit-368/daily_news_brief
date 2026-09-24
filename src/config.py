import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    news_api_key: str = os.getenv("NEWS_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")

    email_from: str = os.getenv("EMAIL_FROM", "")
    email_to: str = os.getenv("EMAIL_TO", "")

    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


settings = Settings()
