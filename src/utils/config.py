"""
Configuration management for DataScope.

This module handles loading and managing configuration from environment
variables and .env files.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

from .exceptions import MissingConfigError
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class Config:
    """
    Application configuration container.
    
    Attributes:
        google_credentials_path: Path to Google Cloud service account key
        mastodon_instance: Default Mastodon instance URL
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        output_dir: Directory for output files
        data_dir: Directory for data files
        log_dir: Directory for log files
    """
    
    # Google Cloud
    google_credentials_path: Optional[str] = None
    
    # Mastodon
    mastodon_instance: str = "https://mastodon.social"
    
    # Logging
    log_level: str = "INFO"
    
    # Directories
    output_dir: Path = field(default_factory=lambda: Path("./outputs"))
    data_dir: Path = field(default_factory=lambda: Path("./data"))
    log_dir: Path = field(default_factory=lambda: Path("./logs"))
    
    # Scraping defaults
    default_limit: int = 100
    
    # Analysis settings
    sentiment_positive_threshold: float = 0.25
    sentiment_negative_threshold: float = -0.25
    max_text_length: int = 5000
    
    def __post_init__(self):
        """Convert string paths to Path objects and create directories."""
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.log_dir, str):
            self.log_dir = Path(self.log_dir)
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def validate(self, require_google_credentials: bool = True) -> None:
        """
        Validate configuration.
        
        Args:
            require_google_credentials: Whether to require Google Cloud credentials
            
        Raises:
            MissingConfigError: If required configuration is missing
        """
        if require_google_credentials and not self.google_credentials_path:
            raise MissingConfigError("GOOGLE_APPLICATION_CREDENTIALS")
        
        if require_google_credentials and self.google_credentials_path:
            creds_path = Path(self.google_credentials_path)
            if not creds_path.exists():
                raise MissingConfigError(
                    f"GOOGLE_APPLICATION_CREDENTIALS dosyası bulunamadı: {creds_path}"
                )


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file: Path to .env file (optional)
        
    Returns:
        Config: Loaded configuration
        
    Example:
        >>> config = load_config()
        >>> print(config.mastodon_instance)
        https://mastodon.social
    """
    # Load .env file if exists
    if env_file:
        load_dotenv(env_file)
    else:
        # Try to find .env in project root
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f".env dosyası yüklendi: {env_path}")
    
    # Build configuration from environment variables
    config = Config(
        google_credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        mastodon_instance=os.getenv("MASTODON_INSTANCE", "https://mastodon.social"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        output_dir=Path(os.getenv("OUTPUT_DIR", "./outputs")),
        data_dir=Path(os.getenv("DATA_DIR", "./data")),
        log_dir=Path(os.getenv("LOG_DIR", "./logs")),
        default_limit=int(os.getenv("DEFAULT_LIMIT", "100")),
        sentiment_positive_threshold=float(os.getenv("SENTIMENT_POSITIVE_THRESHOLD", "0.25")),
        sentiment_negative_threshold=float(os.getenv("SENTIMENT_NEGATIVE_THRESHOLD", "-0.25")),
        max_text_length=int(os.getenv("MAX_TEXT_LENGTH", "5000")),
    )
    
    logger.info("Yapılandırma yüklendi")
    logger.debug(f"Mastodon instance: {config.mastodon_instance}")
    logger.debug(f"Log level: {config.log_level}")
    
    return config


# Global configuration instance (lazy loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: Global configuration
        
    Example:
        >>> config = get_config()
        >>> print(config.output_dir)
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None


