from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    DATABASE_URL: str = ""
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "papers"
    LLM_PROVIDER: str = "groq"  
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""              
    NEWSAPI_KEY: str = ""
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  
    QDRANT_API_KEY: str = ""
    class Config:
        env_file = ".env"
        extra: "allow"
    


settings = Settings()