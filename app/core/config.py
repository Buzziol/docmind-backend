from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "DocMind API"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://docmind:docmind@localhost:5433/docmind"
    API_PREFIX: str = ""
    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    UPLOAD_DIR: str = "uploads/documents"
    MAX_UPLOAD_SIZE_MB: int = 10

    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200

    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"

    RAG_TOP_K: int = 5
    RAG_MAX_CONTEXT_CHARS: int = 8000

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()