"""
Tests for the Mastodon scraper module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.scraper.mastodon import MastodonScraper
from src.scraper.base import BaseScraper
from src.utils.exceptions import (
    InvalidInstanceError,
    HashtagNotFoundError,
    RateLimitError,
    ConnectionError,
)


class TestMastodonScraperInit:
    """Tests for MastodonScraper initialization."""
    
    @patch('src.scraper.mastodon.Mastodon')
    def test_valid_instance_url(self, mock_mastodon):
        """Test initialization with valid instance URL."""
        mock_client = Mock()
        mock_client.instance.return_value = {'title': 'Test Instance'}
        mock_mastodon.return_value = mock_client
        
        scraper = MastodonScraper("https://mastodon.social")
        
        assert scraper.instance_url == "https://mastodon.social"
        mock_mastodon.assert_called_once_with(api_base_url="https://mastodon.social")
    
    def test_invalid_instance_url_empty(self):
        """Test error with empty instance URL."""
        with pytest.raises(InvalidInstanceError):
            MastodonScraper("")
    
    def test_invalid_instance_url_no_protocol(self):
        """Test error with URL missing protocol."""
        with pytest.raises(InvalidInstanceError):
            MastodonScraper("mastodon.social")


class TestMastodonScraperFetch:
    """Tests for MastodonScraper fetch methods."""
    
    @patch('src.scraper.mastodon.Mastodon')
    def test_fetch_by_hashtag_success(self, mock_mastodon, mock_mastodon_response):
        """Test successful hashtag fetch."""
        mock_client = Mock()
        mock_client.instance.return_value = {'title': 'Test Instance'}
        mock_client.timeline_hashtag.return_value = mock_mastodon_response
        mock_mastodon.return_value = mock_client
        
        scraper = MastodonScraper("https://mastodon.social")
        posts = scraper.fetch_by_hashtag("iklim", limit=5)
        
        assert len(posts) == 1
        assert posts[0]['id'] == '12345'
        assert 'text' in posts[0]
        assert 'author' in posts[0]
    
    @patch('src.scraper.mastodon.Mastodon')
    def test_fetch_by_hashtag_strips_hash(self, mock_mastodon, mock_mastodon_response):
        """Test that # is stripped from hashtag."""
        mock_client = Mock()
        mock_client.instance.return_value = {'title': 'Test Instance'}
        mock_client.timeline_hashtag.return_value = mock_mastodon_response
        mock_mastodon.return_value = mock_client
        
        scraper = MastodonScraper("https://mastodon.social")
        scraper.fetch_by_hashtag("#iklim", limit=5)
        
        # Should be called with "iklim" not "#iklim"
        mock_client.timeline_hashtag.assert_called()
        call_args = mock_client.timeline_hashtag.call_args
        assert call_args[0][0] == "iklim"
    
    @patch('src.scraper.mastodon.Mastodon')
    def test_fetch_by_hashtag_empty_result(self, mock_mastodon):
        """Test fetch with no results."""
        mock_client = Mock()
        mock_client.instance.return_value = {'title': 'Test Instance'}
        mock_client.timeline_hashtag.return_value = []
        mock_mastodon.return_value = mock_client
        
        scraper = MastodonScraper("https://mastodon.social")
        posts = scraper.fetch_by_hashtag("nonexistent", limit=5)
        
        assert posts == []
    
    def test_fetch_empty_hashtag(self):
        """Test error with empty hashtag."""
        with patch('src.scraper.mastodon.Mastodon') as mock_mastodon:
            mock_client = Mock()
            mock_client.instance.return_value = {'title': 'Test Instance'}
            mock_mastodon.return_value = mock_client
            
            scraper = MastodonScraper("https://mastodon.social")
            
            with pytest.raises(ValueError):
                scraper.fetch_by_hashtag("", limit=5)


class TestMastodonScraperNormalization:
    """Tests for post normalization."""
    
    @patch('src.scraper.mastodon.Mastodon')
    def test_normalize_post(self, mock_mastodon):
        """Test post normalization."""
        mock_client = Mock()
        mock_client.instance.return_value = {'title': 'Test Instance'}
        mock_mastodon.return_value = mock_client
        
        scraper = MastodonScraper("https://mastodon.social")
        
        raw_post = {
            'id': 12345,
            'content': '<p>Test <b>post</b></p>',
            'account': {'acct': 'testuser'},
            'created_at': datetime.now(),
            'reblogs_count': 5,
            'favourites_count': 10,
            'replies_count': 2,
            'url': 'https://example.com/post',
            'language': 'tr',
            'visibility': 'public',
        }
        
        normalized = scraper._normalize_post(raw_post)
        
        assert normalized['id'] == '12345'
        assert 'Test' in normalized['text']
        assert 'post' in normalized['text']
        assert '<p>' not in normalized['text']
        assert normalized['author'] == 'testuser'
        assert normalized['reblogs_count'] == 5


class TestMastodonScraperHtmlCleaning:
    """Tests for HTML cleaning in scraper."""
    
    @patch('src.scraper.mastodon.Mastodon')
    def test_clean_html_basic(self, mock_mastodon):
        """Test basic HTML cleaning."""
        mock_client = Mock()
        mock_client.instance.return_value = {'title': 'Test Instance'}
        mock_mastodon.return_value = mock_client
        
        scraper = MastodonScraper("https://mastodon.social")
        
        html = "<p>Hello <b>world</b></p>"
        result = scraper._clean_html(html)
        
        assert "Hello" in result
        assert "world" in result
        assert "<p>" not in result
    
    @patch('src.scraper.mastodon.Mastodon')
    def test_clean_html_empty(self, mock_mastodon):
        """Test cleaning empty HTML."""
        mock_client = Mock()
        mock_client.instance.return_value = {'title': 'Test Instance'}
        mock_mastodon.return_value = mock_client
        
        scraper = MastodonScraper("https://mastodon.social")
        
        assert scraper._clean_html("") == ""
        assert scraper._clean_html(None) == ""


class TestBaseScraper:
    """Tests for the base scraper class."""
    
    def test_base_scraper_is_abstract(self):
        """Test that BaseScraper cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseScraper("https://example.com")
    
    def test_base_scraper_repr(self):
        """Test BaseScraper repr through subclass."""
        with patch('src.scraper.mastodon.Mastodon') as mock_mastodon:
            mock_client = Mock()
            mock_client.instance.return_value = {'title': 'Test'}
            mock_mastodon.return_value = mock_client
            
            scraper = MastodonScraper("https://mastodon.social")
            repr_str = repr(scraper)
            
            assert "MastodonScraper" in repr_str
            assert "mastodon.social" in repr_str


