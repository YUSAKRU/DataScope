"""
Base scraper class for DataScope.

This module defines the abstract base class for all scrapers,
providing a common interface for data collection.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from ..utils.logger import LoggerMixin


class BaseScraper(ABC, LoggerMixin):
    """
    Abstract base class for all scrapers.
    
    This class defines the common interface that all scrapers must implement.
    Subclasses should override the abstract methods to provide platform-specific
    implementations.
    
    Example:
        >>> class MyScraper(BaseScraper):
        ...     def fetch_by_hashtag(self, hashtag, limit=100):
        ...         # Platform-specific implementation
        ...         pass
    """
    
    def __init__(self, instance_url: str) -> None:
        """
        Initialize the base scraper.
        
        Args:
            instance_url: The URL of the platform instance
        """
        self.instance_url = instance_url
        self.logger.debug(f"BaseScraper initialized with instance: {instance_url}")
    
    @abstractmethod
    def fetch_by_hashtag(self, hashtag: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch posts by hashtag.
        
        This method must be implemented by all subclasses to provide
        platform-specific data fetching logic.
        
        Args:
            hashtag: The hashtag to search for (without # symbol)
            limit: Maximum number of posts to fetch (default: 100)
            
        Returns:
            List[Dict]: List of posts. Each post must contain at minimum:
                - id: str - Unique post identifier
                - text: str - Post content
                - author: str - Author username
                - created_at: str - Creation timestamp (ISO 8601)
                
        Raises:
            ScraperError: If fetching fails
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate connection to the platform instance.
        
        Returns:
            bool: True if connection is valid
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        pass
    
    def _normalize_post(self, raw_post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw post to the standard format.
        
        Subclasses can override this method to provide platform-specific
        normalization logic.
        
        Args:
            raw_post: Raw post data from the platform
            
        Returns:
            Dict: Normalized post data
        """
        return raw_post
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(instance_url='{self.instance_url}')"


