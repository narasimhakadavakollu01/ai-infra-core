from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Platform API"
    SECRET_KEY: str = "your-very-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_URL: str = "redis://localhost:6379"
    
    # Ikada credentials marchu bava - matches Docker config
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_db"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "documents"

    model_config = {"env_file": ".env"} # Modern Pydantic style

settings = Settings()