from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "papers"
    LLM_PROVIDER: str = "groq"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    GROQ_API_KEY: str = ""
    NEWSAPI_KEY: str = ""

    model_config = {
        "env_file": ".env",     # ✅ load .env
        "extra": "allow"        # ✅ ignore extra fields (FIXES YOUR ERROR)
    }

settings = Settings()