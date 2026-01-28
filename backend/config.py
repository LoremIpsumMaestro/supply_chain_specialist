"""Application configuration."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# Try to load from multiple locations (backend/.env, then root .env)
backend_env = Path(__file__).parent / ".env"
root_env = Path(__file__).parent.parent / ".env"

if backend_env.exists():
    load_dotenv(backend_env)
elif root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()  # Try current directory


class Settings:
    """Application settings loaded from environment variables."""

    # Database (SQLite par défaut pour développement, PostgreSQL pour production)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./supply_chain_ai.db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "supply-chain-files")

    # TypeSense
    TYPESENSE_HOST: str = os.getenv("TYPESENSE_HOST", "localhost")
    TYPESENSE_PORT: int = int(os.getenv("TYPESENSE_PORT", "8108"))
    TYPESENSE_API_KEY: str = os.getenv("TYPESENSE_API_KEY", "xyz123")
    TYPESENSE_PROTOCOL: str = os.getenv("TYPESENSE_PROTOCOL", "http")

    # Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    OLLAMA_CHAT_MODEL: str = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # File Upload
    MAX_FILE_SIZE_BYTES: int = 52428800  # 50MB
    ALLOWED_EXTENSIONS: set[str] = {'.xlsx', '.xls', '.csv', '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.txt'}

    # Rate Limiting
    RATE_LIMIT_UPLOADS_PER_MINUTE: int = 10
    RATE_LIMIT_MESSAGES_PER_MINUTE: int = 10
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5


settings = Settings()
