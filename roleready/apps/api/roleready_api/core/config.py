from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    ALLOW_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",  # Add port 3002
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",  # Add port 3002
        "http://192.168.1.160:3002"  # Add network IP
    ]
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()

def get_settings():
    """Get application settings"""
    return settings
