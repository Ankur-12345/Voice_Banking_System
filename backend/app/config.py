from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./voice_banking.db"
    
    # Groq AI Configuration (FREE!)
    GROQ_API_KEY: str = ""  # Set in .env file
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Updated to latest model
    
    # SMTP Settings (optional, for email features)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
