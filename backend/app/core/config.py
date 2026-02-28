from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost/innovate_db"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "papers"
    LLM_PROVIDER: str = "openai"  # swap to "anthropic" anytime
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # free, local, good enough

    class Config:
        env_file = ".env"

settings = Settings()
