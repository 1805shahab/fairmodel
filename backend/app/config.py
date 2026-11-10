from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    app_env: Literal["development", "test"] = "development"
    database_url: str = "sqlite:///./fairmodel.db"
    storage_dir: Path = Path("storage")
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.1-flash-lite"
    groq_api_key: SecretStr = SecretStr("")
    groq_whisper_model: str = "whisper-large-v3-turbo"
    payment_provider: Literal["mock", "paypal_sandbox"] = "mock"
    paypal_client_id: SecretStr = SecretStr("")
    paypal_client_secret: SecretStr = SecretStr("")
    paypal_environment: Literal["sandbox"] = "sandbox"
    paypal_webhook_id: SecretStr = SecretStr("")
    paypal_sandbox_merchant_email: str = ""
    paypal_sandbox_buyer_email: str = ""
    paypal_allow_drafts: bool = False
    paypal_allow_sending: bool = False
    enable_speaker_verification: bool = False
    demo_mode: bool = True
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"
    frontend_origin: str = "http://localhost:3000"
    max_upload_mb: int = Field(default=24, ge=1, le=24)
    max_audio_seconds: int = Field(default=600, ge=1, le=600)

    @model_validator(mode="after")
    def local_only(self):
        if not self.demo_mode:
            raise ValueError("Production authentication is not implemented. DEMO_MODE must remain true.")
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError("This development schema supports local SQLite only.")
        return self


settings = Settings()
