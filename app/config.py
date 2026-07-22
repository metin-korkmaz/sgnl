"""Centralized configuration using Pydantic.

All environment variables are centralized here for maintainability.
Import the `config` singleton instead of using os.getenv() directly.
"""

import os
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Config(BaseModel):
    """SGNL application configuration.

    All environment variables are loaded and validated here.
    Default values match the existing behavior to maintain backward compatibility.
    """

    # ============ Database ============
    DATABASE_URL: str = Field(default="sqlite:///./analytics.db")

    # ============ API Keys ============
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    TAVILY_API_KEY: Optional[str] = Field(default=None)

    # ============ n8n Workflows ============
    N8N_WEBHOOK_URL: Optional[str] = Field(default=None)
    N8N_FAST_SEARCH_URL: Optional[str] = Field(default=None)

    # ============ Rate Limiting ============
    RATE_LIMIT: int = Field(default=3, ge=1)
    RATE_WINDOW_SECONDS: int = Field(default=60, ge=1)
    TRUSTED_PROXIES: str = Field(default="")
    AUTH_BYPASS_RATE_LIMIT: bool = Field(default=False)

    # ============ CORS Configuration ============
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000")

    # ============ Server Configuration ============
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000, ge=1, le=65535)
    LOG_LEVEL: str = Field(default="INFO")

    # ============ Content Extraction ============
    DENSITY_THRESHOLD: float = Field(default=0.45, ge=0.0, le=1.0)
    LLM_MAX_CHARS: int = Field(default=12000, ge=1000)
    FAST_SEARCH_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1.0)
    SCAN_TOPIC_TIMEOUT_SECONDS: float = Field(default=180.0, ge=1.0)

    # ============ Density Weights (sum should be 1.0) ============
    CPIDR_WEIGHT: float = Field(default=0.5, ge=0.0, le=1.0)
    DEPID_WEIGHT: float = Field(default=0.3, ge=0.0, le=1.0)
    READABILITY_WEIGHT: float = Field(default=0.2, ge=0.0, le=1.0)

    # ============ Cache Configuration ============
    CACHE_MAX_SIZE: int = Field(default=1000, ge=1)
    CACHE_TTL_FAST_SEARCH: int = Field(default=3600, ge=1)
    CACHE_TTL_SCAN_TOPIC: int = Field(default=3600, ge=1)

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got {v}")
        return v_upper

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list of strings."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def TRUSTED_PROXIES_LIST(self) -> List[str]:
        """Get TRUSTED_PROXIES as a list of strings."""
        if not self.TRUSTED_PROXIES:
            return []
        return [proxy.strip() for proxy in self.TRUSTED_PROXIES.split(",")]

    model_config = ConfigDict(populate_by_name=True)


def _load_from_env() -> dict:
    """Load configuration from environment variables.

    Returns a dictionary with values from environment variables or defaults.
    """
    return {
        # Database
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./analytics.db"),
        # API Keys
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
        # n8n Workflows
        "N8N_WEBHOOK_URL": os.getenv("N8N_WEBHOOK_URL"),
        "N8N_FAST_SEARCH_URL": os.getenv("N8N_FAST_SEARCH_URL"),
        # Rate Limiting
        "RATE_LIMIT": int(os.getenv("RATE_LIMIT", "3")),
        "RATE_WINDOW_SECONDS": int(os.getenv("RATE_WINDOW_SECONDS", "60")),
        "TRUSTED_PROXIES": os.getenv("TRUSTED_PROXIES", ""),
        "AUTH_BYPASS_RATE_LIMIT": os.getenv("AUTH_BYPASS_RATE_LIMIT", "false").lower() == "true",
        # CORS
        "ALLOWED_ORIGINS": os.getenv("ALLOWED_ORIGINS", "http://localhost:3000"),
        # Server
        "HOST": os.getenv("HOST", "0.0.0.0"),
        "PORT": int(os.getenv("PORT", "8000")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        # Content Extraction
        "DENSITY_THRESHOLD": float(os.getenv("DENSITY_THRESHOLD", "0.45")),
        "LLM_MAX_CHARS": int(os.getenv("LLM_MAX_CHARS", "12000")),
        "FAST_SEARCH_TIMEOUT_SECONDS": float(os.getenv("FAST_SEARCH_TIMEOUT_SECONDS", "30")),
        "SCAN_TOPIC_TIMEOUT_SECONDS": float(os.getenv("SCAN_TOPIC_TIMEOUT_SECONDS", "180")),
        # Density Weights
        "CPIDR_WEIGHT": float(os.getenv("CPIDR_WEIGHT", "0.5")),
        "DEPID_WEIGHT": float(os.getenv("DEPID_WEIGHT", "0.3")),
        "READABILITY_WEIGHT": float(os.getenv("READABILITY_WEIGHT", "0.2")),
        # Cache
        "CACHE_MAX_SIZE": int(os.getenv("CACHE_MAX_SIZE", "1000")),
        "CACHE_TTL_FAST_SEARCH": int(os.getenv("CACHE_TTL_FAST_SEARCH", "3600")),
        "CACHE_TTL_SCAN_TOPIC": int(os.getenv("CACHE_TTL_SCAN_TOPIC", "3600")),
    }


# Singleton instance - import this in other modules
config = Config(**_load_from_env())


def get_config() -> Config:
    """Get the configuration singleton.

    Returns:
        Config instance with all validated environment variables.
    """
    return config


def reload_config() -> Config:
    """Reload configuration from environment.

    Useful for testing or when environment variables change at runtime.

    Returns:
        Fresh Config instance.
    """
    global config
    config = Config(**_load_from_env())
    return config
