"""
Logging configuration for DataScope.

This module provides a centralized logging setup with colored console output
and file logging capabilities.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Color format for console output
COLOR_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s"

# Log colors mapping
LOG_COLORS = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}


def setup_logger(
    name: str = "ika-vms",
    level: str = "INFO",
    log_dir: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Logger name (default: "ika-vms")
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        console_output: Enable console output (default: True)
        file_output: Enable file output (default: True)
        
    Returns:
        logging.Logger: Configured logger instance
        
    Example:
        >>> logger = setup_logger("my-module", level="DEBUG")
        >>> logger.info("Application started")
        >>> logger.error("An error occurred", exc_info=True)
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Console handler with colors
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if HAS_COLORLOG:
            console_formatter = colorlog.ColoredFormatter(
                COLOR_FORMAT,
                datefmt=DEFAULT_DATE_FORMAT,
                log_colors=LOG_COLORS
            )
        else:
            console_formatter = logging.Formatter(
                DEFAULT_FORMAT,
                datefmt=DEFAULT_DATE_FORMAT
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
        else:
            log_dir = Path(log_dir)
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        log_file = log_dir / f"ika-vms_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            DEFAULT_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "ika-vms") -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
        
    Example:
        >>> logger = get_logger("my-module")
        >>> logger.info("Processing started")
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


class LoggerMixin:
    """
    Mixin class that provides logging capabilities to any class.
    
    Example:
        >>> class MyClass(LoggerMixin):
        ...     def do_something(self):
        ...         self.logger.info("Doing something")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_function_call(func):
    """
    Decorator to log function entry and exit.
    
    Example:
        >>> @log_function_call
        ... def my_function(x, y):
        ...     return x + y
    """
    logger = get_logger(func.__module__)
    
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    
    return wrapper


