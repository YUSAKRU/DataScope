"""
Tests for the data cleaning module.
"""

import pytest
import pandas as pd

from src.processor.cleaning import (
    clean_html,
    clean_urls,
    clean_mentions,
    clean_hashtags,
    clean_special_characters,
    normalize_whitespace,
    clean_text,
    process_dataframe,
    validate_dataframe,
    remove_stopwords,
    get_word_frequencies,
)
from src.utils.exceptions import MissingColumnError


class TestCleanHtml:
    """Tests for HTML cleaning function."""
    
    def test_clean_simple_html(self):
        """Test cleaning simple HTML tags."""
        html = "<p>Merhaba <b>dünya</b></p>"
        result = clean_html(html)
        assert "Merhaba" in result
        assert "dünya" in result
        assert "<p>" not in result
        assert "<b>" not in result
    
    def test_clean_html_with_br(self):
        """Test cleaning HTML with line breaks."""
        html = "<p>Satır 1<br>Satır 2</p>"
        result = clean_html(html)
        assert "Satır 1" in result
        assert "Satır 2" in result
    
    def test_clean_empty_html(self):
        """Test cleaning empty string."""
        assert clean_html("") == ""
        assert clean_html(None) == ""


class TestCleanUrls:
    """Tests for URL cleaning function."""
    
    def test_clean_https_url(self):
        """Test cleaning HTTPS URLs."""
        text = "Check this https://example.com out"
        result = clean_urls(text)
        assert "https://example.com" not in result
        assert "Check this" in result
    
    def test_clean_http_url(self):
        """Test cleaning HTTP URLs."""
        text = "Visit http://test.org for more"
        result = clean_urls(text)
        assert "http://test.org" not in result
    
    def test_clean_www_url(self):
        """Test cleaning www URLs."""
        text = "Go to www.example.com now"
        result = clean_urls(text)
        assert "www.example.com" not in result
    
    def test_preserve_text_without_urls(self):
        """Test that text without URLs is preserved."""
        text = "Normal text without any links"
        result = clean_urls(text)
        assert result == text


class TestCleanMentions:
    """Tests for mention cleaning function."""
    
    def test_clean_simple_mention(self):
        """Test cleaning simple @mentions."""
        text = "Hello @user how are you"
        result = clean_mentions(text)
        assert "@user" not in result
        assert "Hello" in result
    
    def test_clean_federated_mention(self):
        """Test cleaning federated @user@instance mentions."""
        text = "Reply to @user@mastodon.social"
        result = clean_mentions(text)
        assert "@user@mastodon.social" not in result


class TestCleanHashtags:
    """Tests for hashtag cleaning function."""
    
    def test_clean_hashtag_keep_word(self):
        """Test cleaning hashtag but keeping word."""
        text = "#iklim değişikliği #önemli"
        result = clean_hashtags(text, keep_word=True)
        assert "#" not in result
        assert "iklim" in result
        assert "önemli" in result
    
    def test_clean_hashtag_remove_all(self):
        """Test removing entire hashtag."""
        text = "#iklim değişikliği #önemli"
        result = clean_hashtags(text, keep_word=False)
        assert "iklim" not in result
        assert "değişikliği" in result


class TestCleanText:
    """Tests for the full text cleaning function."""
    
    def test_clean_complex_text(self):
        """Test cleaning complex text with multiple elements."""
        raw = "<p>@user check https://example.com #iklim değişikliği!</p>"
        result = clean_text(raw)
        
        # Should not contain these
        assert "@user" not in result
        assert "https://example.com" not in result
        assert "<p>" not in result
        
        # Should contain these
        assert "iklim" in result
        assert "değişikliği" in result
    
    def test_clean_empty_text(self):
        """Test cleaning empty text."""
        assert clean_text("") == ""
        assert clean_text(None) == ""


class TestNormalizeWhitespace:
    """Tests for whitespace normalization."""
    
    def test_multiple_spaces(self):
        """Test normalizing multiple spaces."""
        text = "Hello    world"
        result = normalize_whitespace(text)
        assert result == "Hello world"
    
    def test_multiple_newlines(self):
        """Test normalizing multiple newlines."""
        text = "Line 1\n\n\nLine 2"
        result = normalize_whitespace(text)
        assert result == "Line 1\nLine 2"
    
    def test_strip_whitespace(self):
        """Test stripping leading/trailing whitespace."""
        text = "  Hello world  "
        result = normalize_whitespace(text)
        assert result == "Hello world"


class TestProcessDataFrame:
    """Tests for DataFrame processing."""
    
    def test_process_dataframe_success(self, sample_dataframe):
        """Test successful DataFrame processing."""
        result = process_dataframe(sample_dataframe)
        
        assert 'cleaned_text' in result.columns
        assert 'text_length' in result.columns
        assert len(result) == len(sample_dataframe)
    
    def test_process_dataframe_missing_column(self):
        """Test error when required column is missing."""
        df = pd.DataFrame({'id': [1], 'author': ['user']})
        
        with pytest.raises(MissingColumnError):
            process_dataframe(df)


class TestValidateDataFrame:
    """Tests for DataFrame validation."""
    
    def test_validate_success(self, sample_dataframe):
        """Test successful validation."""
        # Should not raise
        validate_dataframe(sample_dataframe)
    
    def test_validate_missing_column(self):
        """Test validation with missing column."""
        df = pd.DataFrame({'id': [1], 'text': ['hello']})
        
        with pytest.raises(MissingColumnError):
            validate_dataframe(df)


class TestRemoveStopwords:
    """Tests for stopword removal."""
    
    def test_remove_turkish_stopwords(self):
        """Test removing Turkish stopwords."""
        text = "bu bir çok önemli konu"
        result = remove_stopwords(text)
        
        assert "bu" not in result.split()
        assert "bir" not in result.split()
        assert "önemli" in result
        assert "konu" in result


class TestGetWordFrequencies:
    """Tests for word frequency calculation."""
    
    def test_word_frequencies(self):
        """Test word frequency calculation."""
        texts = ["iklim değişikliği", "iklim krizi", "iklim"]
        freqs = get_word_frequencies(texts)
        
        assert "iklim" in freqs
        assert freqs["iklim"] == 3
        assert "değişikliği" in freqs
        assert freqs["değişikliği"] == 1


