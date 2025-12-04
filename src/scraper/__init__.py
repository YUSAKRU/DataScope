"""
Scraper modules for DataScope.

This package contains scrapers for different social media platforms.
Currently supported:
- Mastodon (Fediverse)

Also includes:
- HashtagSuggester: Intelligent hashtag recommendation system
"""

from .base import BaseScraper
from .mastodon import MastodonScraper
from .hashtag_suggester import HashtagSuggester, suggest_hashtags

__all__ = [
    "BaseScraper",
    "MastodonScraper",
    "HashtagSuggester",
    "suggest_hashtags",
]


