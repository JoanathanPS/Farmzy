"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Supabase PostgreSQL Database URL
    # Format: postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
    database_url: Optional[str] = None
    
    # Supabase API (optional - for direct Supabase client usage)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    # Redis (Optional)
    redis_url: Optional[str] = None
    
    # ThingSpeak API
    thingspeak_api_key: Optional[str] = None
    thingspeak_channel_id: Optional[str] = None
    thingspeak_read_api_key: Optional[str] = None
    
    # Weather API (OpenWeatherMap)
    weather_api_key: Optional[str] = None
    
    # JWT
    secret_key: str = "farmzy-secure-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # App
    app_name: str = "Farmzy"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
