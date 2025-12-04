"""
Mastodon scraper module for DataScope.

This module provides the MastodonScraper class for fetching posts
from Mastodon instances via their public API.
"""

import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from mastodon import Mastodon, MastodonNetworkError, MastodonAPIError
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..utils.exceptions import (
    HashtagNotFoundError,
    RateLimitError,
    InvalidInstanceError,
    ConnectionError,
    ScraperError,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MastodonScraper(BaseScraper):
    """
    Scraper for fetching data from Mastodon instances.
    
    This class uses the Mastodon.py library to interact with the Mastodon API.
    It supports fetching posts by hashtag and handles rate limiting and errors.
    
    Example:
        >>> scraper = MastodonScraper(instance_url="https://mastodon.social")
        >>> posts = scraper.fetch_by_hashtag(hashtag="iklim", limit=100)
        >>> for post in posts:
        ...     print(post['text'])
    
    Note:
        The Mastodon API's timeline_hashtag() method requires positional arguments,
        not keyword arguments. This is handled internally by this class.
    """
    
    def __init__(self, instance_url: str) -> None:
        """
        Initialize the Mastodon scraper.
        
        Args:
            instance_url: Mastodon instance URL (e.g., "https://mastodon.social")
            
        Raises:
            InvalidInstanceError: If the URL is invalid
            ConnectionError: If connection to the instance fails
        """
        # Validate URL format
        if not instance_url:
            raise InvalidInstanceError("")
        
        if not instance_url.startswith(("http://", "https://")):
            raise InvalidInstanceError(instance_url)
        
        super().__init__(instance_url)
        
        # Initialize Mastodon client
        try:
            self._client = Mastodon(api_base_url=instance_url)
            self.logger.info(f"Mastodon client initialized for: {instance_url}")
        except Exception as e:
            raise ConnectionError(instance_url, str(e))
        
        # Validate connection
        self.validate_connection()
    
    def validate_connection(self) -> bool:
        """
        Validate connection to the Mastodon instance.
        
        Returns:
            bool: True if connection is valid
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        try:
            # Try to get instance info to validate connection
            instance_info = self._client.instance()
            self.logger.debug(f"Connected to instance: {instance_info.get('title', 'Unknown')}")
            return True
        except MastodonNetworkError as e:
            raise ConnectionError(self.instance_url, str(e))
        except Exception as e:
            raise ConnectionError(self.instance_url, str(e))
    
    def fetch_by_hashtag(self, hashtag: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch posts by hashtag from Mastodon.
        
        Args:
            hashtag: The hashtag to search for (without # symbol)
                     Examples: "iklim", "İklimKanunu"
            limit: Maximum number of posts to fetch (default: 100)
            
        Returns:
            List[Dict]: List of posts. Each post contains:
                - id: str - Post ID
                - text: str - Post text (HTML cleaned)
                - author: str - Author username
                - created_at: str - Creation timestamp (ISO 8601)
                - reblogs_count: int - Number of reblogs
                - favourites_count: int - Number of favourites
                - replies_count: int - Number of replies
                - instance: str - Source instance URL
                - url: str - Post URL
                
        Raises:
            HashtagNotFoundError: If the hashtag is not found
            RateLimitError: If rate limit is exceeded
            ScraperError: For other API errors
        """
        # Clean hashtag (remove # if present)
        hashtag = hashtag.lstrip("#").strip()
        
        if not hashtag:
            raise ValueError("Hashtag cannot be empty")
        
        self.logger.info(f"Fetching posts for hashtag: #{hashtag} (limit: {limit})")
        
        posts = []
        max_id = None
        remaining = limit
        
        try:
            while remaining > 0:
                # Fetch a batch of posts
                # IMPORTANT: timeline_hashtag() requires positional argument!
                batch_limit = min(remaining, 40)  # Mastodon API max per request
                
                if max_id:
                    timeline = self._client.timeline_hashtag(hashtag, max_id=max_id, limit=batch_limit)
                else:
                    timeline = self._client.timeline_hashtag(hashtag, limit=batch_limit)
                
                if not timeline:
                    self.logger.debug("No more posts available")
                    break
                
                # Process each post
                for status in timeline:
                    normalized_post = self._normalize_post(status)
                    posts.append(normalized_post)
                    remaining -= 1
                    
                    if remaining <= 0:
                        break
                
                # Get max_id for pagination
                if timeline:
                    max_id = timeline[-1]['id']
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
                self.logger.debug(f"Fetched {len(posts)} posts so far...")
            
            self.logger.info(f"Successfully fetched {len(posts)} posts for #{hashtag}")
            return posts
            
        except MastodonAPIError as e:
            error_str = str(e)
            if "404" in error_str or "Not Found" in error_str:
                raise HashtagNotFoundError(hashtag, self.instance_url)
            elif "429" in error_str or "rate limit" in error_str.lower():
                raise RateLimitError()
            else:
                raise ScraperError(f"Mastodon API error: {error_str}")
        except MastodonNetworkError as e:
            raise ConnectionError(self.instance_url, str(e))
        except Exception as e:
            raise ScraperError(f"Unexpected error while fetching posts: {str(e)}")
    
    def _normalize_post(self, raw_post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a Mastodon status to the standard post format.
        
        Args:
            raw_post: Raw status data from Mastodon API
            
        Returns:
            Dict: Normalized post data
        """
        # Extract text from HTML content
        content = raw_post.get('content', '')
        text = self._clean_html(content)
        
        # Get author info
        account = raw_post.get('account', {})
        author = account.get('acct', account.get('username', 'unknown'))
        
        # Get creation date
        created_at = raw_post.get('created_at')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        elif created_at is None:
            created_at = datetime.now().isoformat()
        
        return {
            'id': str(raw_post.get('id', '')),
            'text': text,
            'author': author,
            'created_at': created_at,
            'reblogs_count': raw_post.get('reblogs_count', 0),
            'favourites_count': raw_post.get('favourites_count', 0),
            'replies_count': raw_post.get('replies_count', 0),
            'instance': self.instance_url,
            'url': raw_post.get('url', ''),
            'language': raw_post.get('language', ''),
            'visibility': raw_post.get('visibility', 'public'),
        }
    
    def _clean_html(self, html_content: str) -> str:
        """
        Remove HTML tags from content.
        
        Args:
            html_content: HTML string
            
        Returns:
            str: Plain text without HTML tags
        """
        if not html_content:
            return ""
        
        # Use BeautifulSoup to parse and extract text
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Replace <br> and <p> tags with newlines
        for br in soup.find_all('br'):
            br.replace_with('\n')
        for p in soup.find_all('p'):
            p.insert_after('\n')
        
        # Get text and clean up whitespace
        text = soup.get_text()
        text = re.sub(r'\n+', '\n', text)  # Multiple newlines to single
        text = text.strip()
        
        return text
    
    def search_hashtags(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for hashtags matching the query.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict]: List of matching hashtags with their info
        """
        try:
            results = self._client.search(query, result_type="hashtags")
            hashtags = results.get('hashtags', [])
            
            return [
                {
                    'name': tag.get('name', ''),
                    'url': tag.get('url', ''),
                    'history': tag.get('history', []),
                }
                for tag in hashtags
            ]
        except Exception as e:
            self.logger.warning(f"Hashtag search failed: {e}")
            return []


