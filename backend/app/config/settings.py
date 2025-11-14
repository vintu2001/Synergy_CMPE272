"""
Central configuration module using Pydantic BaseSettings.
All configuration values are defined here with validation.
"""
import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central configuration for Synergy application.
    Uses Pydantic BaseSettings to load from environment variables.
    """
    
    # ===== Vector Store Configuration =====
    PERSIST_DIR: str = Field(
        default="./vector_stores/chroma_db",
        description="ChromaDB persistence directory"
    )
    COLLECTION_NAME: str = Field(
        default="apartment_kb",
        description="ChromaDB collection name"
    )
    
    # ===== Embedding Configuration =====
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace embedding model"
    )
    EMBEDDING_DEVICE: str = Field(
        default="cpu",
        description="Device for embeddings (cpu/cuda/mps)"
    )
    EMBEDDING_DIMENSION: int = Field(
        default=384,
        description="Embedding vector dimension"
    )
    
    # ===== Chunking Configuration =====
    CHUNK_SIZE: int = Field(
        default=700,
        description="Text chunk size in characters",
        ge=100,
        le=2000
    )
    CHUNK_OVERLAP: int = Field(
        default=120,
        description="Overlap between chunks",
        ge=0,
        le=500
    )
    
    # ===== Retrieval Configuration =====
    RETRIEVAL_K: int = Field(
        default=5,
        description="Number of documents to retrieve",
        ge=1,
        le=50
    )
    FETCH_K: int = Field(
        default=20,
        description="Number of documents to fetch before MMR filtering",
        ge=1,
        le=100
    )
    LAMBDA_MULT: float = Field(
        default=0.5,
        description="MMR diversity parameter (0=max diversity, 1=max similarity)",
        ge=0.0,
        le=1.0
    )
    SIMILARITY_CUTOFF: Optional[float] = Field(
        default=0.7,
        description="Minimum similarity threshold for retrieval",
        ge=0.0,
        le=1.0
    )
    MAX_CONTEXT_TOKENS: int = Field(
        default=3000,
        description="Maximum tokens for LLM context",
        ge=100,
        le=100000
    )
    
    # ===== LLM Configuration =====
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-pro",
        description="Google Gemini model name"
    )
    GOOGLE_API_KEY: str = Field(
        ...,
        description="Google API key for Gemini (required)"
    )
    GEMINI_API_KEY: str = Field(
        ...,
        description="Backward compatibility alias for Google API key (required)"
    )
    TEMPERATURE: float = Field(
        default=0.0,
        description="LLM temperature (0=deterministic, 2=creative)",
        ge=0.0,
        le=2.0
    )
    GEMINI_MAX_TOKENS: int = Field(
        default=2048,
        description="Maximum tokens for LLM response",
        ge=1,
        le=8192
    )
    GEMINI_TIMEOUT: int = Field(
        default=60,
        description="Timeout for LLM requests in seconds",
        ge=1,
        le=300
    )
    GEMINI_SAFETY_LEVEL: str = Field(
        default="BLOCK_ONLY_HIGH",
        description="Safety filtering level (BLOCK_NONE, BLOCK_ONLY_HIGH, BLOCK_MEDIUM_AND_ABOVE, BLOCK_LOW_AND_ABOVE)"
    )
    
    # ===== Feature Toggles =====
    RAG_ENABLED: bool = Field(
        default=True,
        description="Enable RAG functionality"
    )
    
    # ===== AWS/DynamoDB Configuration =====
    AWS_REGION: str = Field(
        default="us-west-2",
        description="AWS region"
    )
    AWS_DYNAMODB_TABLE_NAME: str = Field(
        default="aam_requests",
        description="DynamoDB table name for requests"
    )
    AWS_DYNAMODB_GOVERNANCE_TABLE: str = Field(
        default="aam_governance_logs",
        description="DynamoDB table name for governance logs"
    )
    AWS_SQS_QUEUE_URL: Optional[str] = Field(
        default=None,
        description="AWS SQS Queue URL for message intake"
    )
    
    # ===== Security Configuration =====
    ADMIN_API_KEY: str = Field(
        default="default-admin-key-change-in-production",
        description="Admin API key for protected endpoints"
    )
    
    # ===== Application Configuration =====
    API_ENVIRONMENT: str = Field(
        default="development",
        description="API environment (development/production)"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra fields from .env
    }
    
    # ===== Validators =====
    
    @field_validator("CHUNK_OVERLAP")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """Ensure chunk overlap is less than chunk size"""
        chunk_size = info.data.get("CHUNK_SIZE", 700)
        if v >= chunk_size:
            raise ValueError(
                f"CHUNK_OVERLAP ({v}) must be less than CHUNK_SIZE ({chunk_size})"
            )
        return v
    
    @field_validator("RETRIEVAL_K")
    @classmethod
    def validate_retrieval_k(cls, v: int, info) -> int:
        """Ensure RETRIEVAL_K is less than or equal to FETCH_K"""
        fetch_k = info.data.get("FETCH_K", 20)
        if v > fetch_k:
            raise ValueError(
                f"RETRIEVAL_K ({v}) must be <= FETCH_K ({fetch_k})"
            )
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure valid log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"LOG_LEVEL must be one of {valid_levels}, got {v}"
            )
        return v_upper


# ===== Singleton Pattern =====

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create settings singleton.
    This ensures configuration is loaded only once.
    
    Returns:
        Settings: The application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Force reload settings from environment.
    Useful for testing or when environment changes.
    
    Returns:
        Settings: The reloaded application settings
    """
    global _settings
    _settings = Settings()
    return _settings


# ===== Utility Functions =====

def print_config(settings: Optional[Settings] = None) -> None:
    """
    Print current configuration settings in a readable format.
    
    Args:
        settings: Settings instance to print (defaults to singleton)
    """
    if settings is None:
        settings = get_settings()
    
    print("=" * 70)
    print("SYNERGY CONFIGURATION")
    print("=" * 70)
    
    print("\n[Vector Store]")
    print(f"  PERSIST_DIR: {settings.PERSIST_DIR}")
    print(f"  COLLECTION_NAME: {settings.COLLECTION_NAME}")
    
    print("\n[Embeddings]")
    print(f"  EMBEDDING_MODEL: {settings.EMBEDDING_MODEL}")
    print(f"  EMBEDDING_DEVICE: {settings.EMBEDDING_DEVICE}")
    print(f"  EMBEDDING_DIMENSION: {settings.EMBEDDING_DIMENSION}")
    
    print("\n[Chunking]")
    print(f"  CHUNK_SIZE: {settings.CHUNK_SIZE}")
    print(f"  CHUNK_OVERLAP: {settings.CHUNK_OVERLAP}")
    
    print("\n[Retrieval]")
    print(f"  RETRIEVAL_K: {settings.RETRIEVAL_K}")
    print(f"  FETCH_K: {settings.FETCH_K}")
    print(f"  LAMBDA_MULT: {settings.LAMBDA_MULT}")
    print(f"  SIMILARITY_CUTOFF: {settings.SIMILARITY_CUTOFF}")
    print(f"  MAX_CONTEXT_TOKENS: {settings.MAX_CONTEXT_TOKENS}")
    
    print("\n[LLM]")
    print(f"  GEMINI_MODEL: {settings.GEMINI_MODEL}")
    print(f"  TEMPERATURE: {settings.TEMPERATURE}")
    print(f"  GEMINI_MAX_TOKENS: {settings.GEMINI_MAX_TOKENS}")
    print(f"  GOOGLE_API_KEY: {'*' * 10}{settings.GOOGLE_API_KEY[-4:]}")
    print(f"  GEMINI_API_KEY: {'*' * 10}{settings.GEMINI_API_KEY[-4:]}")
    
    print("\n[Features]")
    print(f"  RAG_ENABLED: {settings.RAG_ENABLED}")
    
    print("\n[AWS/DynamoDB]")
    print(f"  AWS_REGION: {settings.AWS_REGION}")
    print(f"  AWS_DYNAMODB_TABLE_NAME: {settings.AWS_DYNAMODB_TABLE_NAME}")
    print(f"  AWS_DYNAMODB_GOVERNANCE_TABLE: {settings.AWS_DYNAMODB_GOVERNANCE_TABLE}")
    
    print("\n[Application]")
    print(f"  API_ENVIRONMENT: {settings.API_ENVIRONMENT}")
    print(f"  LOG_LEVEL: {settings.LOG_LEVEL}")
    
    print("\n" + "=" * 70)
