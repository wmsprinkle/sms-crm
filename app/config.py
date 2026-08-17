from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Defaults let the app boot with no accounts for local dev.
    # Fill these in .env when you're ready to send for real.
    database_url: str = "sqlite:///./dev.db"

    telnyx_api_key: str = ""
    telnyx_public_key: str = ""
    telnyx_messaging_profile_id: str = ""
    telnyx_from_number: str = "+10000000000"

    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-v4-flash"

    booking_provider: str = "static"
    calendly_token: str = ""
    calendly_event_type_uri: str = ""
    calendly_signing_key: str = ""
    static_booking_url: str = "https://calendly.com/you/intro"

    quiet_hours_start: int = 21
    quiet_hours_end: int = 9
    auto_send: bool = False
    agency_name: str = "our agency"

    # Worker throughput. Keep at/under your 10DLC campaign's MPS limit.
    # Sustained rate = send_rate_per_minute, spread across each tick.
    worker_interval_seconds: int = 30
    send_rate_per_minute: int = 60

    # When true, no real SMS is sent: messages are logged as if delivered.
    # Defaults to true so a fresh clone runs with nothing configured.
    dry_run: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
