"""Configuration management for the Truth Checker application."""

import os
from typing import Optional
from dotenv import load_dotenv
from dataclasses import dataclass
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # API Keys
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

    # Optional service API keys
    POLITIFACT_API_KEY: Optional[str] = os.getenv("POLITIFACT_API_KEY")
    GOOGLE_FACT_CHECK_API_KEY: Optional[str] = os.getenv("GOOGLE_FACT_CHECK_API_KEY")

    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Deepgram settings
    DEEPGRAM_MODEL: str = os.getenv("DEEPGRAM_MODEL", "nova-3")
    DEEPGRAM_LANGUAGE: str = os.getenv("DEEPGRAM_LANGUAGE", "en-US")
    DEEPGRAM_SMART_FORMAT: bool = os.getenv("DEEPGRAM_SMART_FORMAT", "True").lower() in (
        "true",
        "1",
        "t",
    )

    # Cache settings
    cache_dir: str = os.getenv("CACHE_DIR", "/tmp/truth_checker")


config = Config()


def validate_config() -> list[str]:
    """Validate the configuration and return a list of missing required values.

    Returns:
        List of missing configuration keys
    """
    missing = []
    if not config.DEEPGRAM_API_KEY:
        missing.append("DEEPGRAM_API_KEY")
    if not config.LLM_API_KEY:
        missing.append("LLM_API_KEY")
    return missing 