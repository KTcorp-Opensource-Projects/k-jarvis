"""
Configuration management for Agent Orchestrator
"""
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 4001  # K-Jarvis Backend (4000번대 사용)
    debug: bool = True
    
    # Agent Registry
    registry_host: str = "0.0.0.0"
    registry_port: int = 7000
    
    # ==========================================================================
    # LLM Configuration
    # ==========================================================================
    # LLM Provider: "openai", "azure", "claude", or "gemini"
    llm_provider: Literal["openai", "azure", "claude", "gemini"] = "openai"
    
    # Common LLM Settings
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    
    # OpenAI Configuration (llm_provider = "openai")
    # Available models: gpt-5, gpt-4.1, gpt-4o, gpt-4o-mini, gpt-4-turbo
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    
    # Azure OpenAI Configuration (llm_provider = "azure")
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None  # e.g., "https://your-resource.openai.azure.com/"
    azure_openai_deployment: Optional[str] = None  # Deployment name
    azure_openai_api_version: str = "2024-12-01-preview"  # API version
    
    # Anthropic Claude Configuration (llm_provider = "claude")
    # Available models: claude-sonnet-4-20250514 (latest), claude-3-5-sonnet-20241022, claude-3-opus-20240229
    anthropic_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-20250514"
    
    # Google Gemini Configuration (llm_provider = "gemini")
    # Available models: gemini-2.5-flash (latest), gemini-2.0-flash, gemini-1.5-pro
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    
    # Legacy compatibility (deprecated, use openai_model instead)
    llm_model: str = "gpt-4o"
    
    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "agent_orchestrator"
    db_user: str = ""  # Set via DB_USER environment variable
    db_password: str = ""  # Set via DB_PASSWORD environment variable
    db_echo: bool = False
    db_auto_init: bool = True  # Auto-create schema if tables don't exist
    
    # JWT Configuration (IMPORTANT: Override in production!)
    jwt_secret_key: str = ""  # Set via JWT_SECRET_KEY environment variable
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Logging
    log_level: str = "INFO"
    
    # CORS Configuration
    # 프로덕션에서는 실제 도메인만 허용하도록 설정
    cors_origins: str = "http://localhost:4000,http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> list:
        """CORS 허용 도메인 리스트 반환"""
        origins = self.cors_origins.strip()
        if origins == "*":
            return ["*"]
        return [o.strip() for o in origins.split(",") if o.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

