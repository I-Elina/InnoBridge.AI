from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = ""
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "papers"
    LLM_PROVIDER: str = "groq"  # swap to "anthropic" anytime
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""              # ← add this line
    NEWSAPI_KEY: str = ""
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # free, local, good enough
    QDRANT_API_KEY: str = ""
    class Config:
        env_file = ".env"

settings = Settings()
