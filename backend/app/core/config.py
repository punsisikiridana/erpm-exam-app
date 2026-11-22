from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    admin_password_hash: str = ""
    session_secret: str = "change-me-to-a-long-random-string"
    database_url: str = "sqlite:///./erpm.db"

    mcqmed_access_token: str = ""
    mcqmed_refresh_token: str = ""
    mcqmed_anon_key: str = ""
    mcqmed_supabase_url: str = "https://sqhnejliuqvxiexmazlb.supabase.co"


settings = Settings()
