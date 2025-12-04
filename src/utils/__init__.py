"""
Utility modules for DataScope.

This package contains shared utilities including:
- config: Configuration management
- logger: Logging setup
- exceptions: Custom exception classes
"""

from .config import Config, load_config, get_config, reset_config
from .logger import setup_logger, get_logger, LoggerMixin, log_function_call
from .exceptions import (
    IKAVMSError,
    ScraperError,
    HashtagNotFoundError,
    RateLimitError,
    InvalidInstanceError,
    ConnectionError,
    AnalysisError,
    CredentialsError,
    QuotaExceededError,
    TextTooLongError,
    EmptyTextError,
    ProcessingError,
    MissingColumnError,
    InvalidDataFormatError,
    OutputError,
    FileWriteError,
    FontNotFoundError,
    ConfigurationError,
    MissingConfigError,
)

__all__ = [
    # Config
    "Config",
    "load_config",
    "get_config",
    "reset_config",
    # Logger
    "setup_logger",
    "get_logger",
    "LoggerMixin",
    "log_function_call",
    # Exceptions - Base
    "IKAVMSError",
    # Exceptions - Scraper
    "ScraperError",
    "HashtagNotFoundError",
    "RateLimitError",
    "InvalidInstanceError",
    "ConnectionError",
    # Exceptions - Analysis
    "AnalysisError",
    "CredentialsError",
    "QuotaExceededError",
    "TextTooLongError",
    "EmptyTextError",
    # Exceptions - Processing
    "ProcessingError",
    "MissingColumnError",
    "InvalidDataFormatError",
    # Exceptions - Output
    "OutputError",
    "FileWriteError",
    "FontNotFoundError",
    # Exceptions - Config
    "ConfigurationError",
    "MissingConfigError",
]


