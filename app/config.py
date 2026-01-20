"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Database (Supabase PostgreSQL)
    # Format: postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres
    database_url: str = "postgresql://user:password@localhost:5432/farmzy_db"
    
    # Supabase (optional - for direct Supabase client usage)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None  # Service role key or anon key
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # ThingSpeak API
    thingspeak_api_key: Optional[str] = None
    thingspeak_channel_id: Optional[str] = None
    thingspeak_read_api_key: Optional[str] = None
    
    # Weather API (OpenWeatherMap)
    weather_api_key: Optional[str] = None
    
    # JWT
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # App
    app_name: str = "Farmzy"
    app_version: str = "1.0.0"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

