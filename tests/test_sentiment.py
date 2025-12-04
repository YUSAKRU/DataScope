"""
Tests for the sentiment analysis module.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

from src.analyzer.sentiment import (
    SentimentAnalyzer,
    get_sentiment_summary,
    POSITIVE_THRESHOLD,
    NEGATIVE_THRESHOLD,
)
from src.utils.exceptions import (
    EmptyTextError,
    TextTooLongError,
)


class TestSentimentAnalyzer:
    """Tests for SentimentAnalyzer class."""
    
    def test_analyzer_init_no_credentials(self, monkeypatch):
        """Test analyzer initialization without credentials."""
        monkeypatch.delenv('GOOGLE_APPLICATION_CREDENTIALS', raising=False)
        
        # Should not raise, should use mock mode
        analyzer = SentimentAnalyzer()
        assert analyzer._client is None
    
    def test_score_to_label_positive(self):
        """Test positive score labeling."""
        analyzer = SentimentAnalyzer()
        
        assert analyzer._score_to_label(0.5) == "positive"
        assert analyzer._score_to_label(0.25) == "positive"
        assert analyzer._score_to_label(1.0) == "positive"
    
    def test_score_to_label_negative(self):
        """Test negative score labeling."""
        analyzer = SentimentAnalyzer()
        
        assert analyzer._score_to_label(-0.5) == "negative"
        assert analyzer._score_to_label(-0.25) == "negative"
        assert analyzer._score_to_label(-1.0) == "negative"
    
    def test_score_to_label_neutral(self):
        """Test neutral score labeling."""
        analyzer = SentimentAnalyzer()
        
        assert analyzer._score_to_label(0.0) == "neutral"
        assert analyzer._score_to_label(0.24) == "neutral"
        assert analyzer._score_to_label(-0.24) == "neutral"


class TestMockAnalysis:
    """Tests for mock sentiment analysis."""
    
    def test_mock_analyze_positive(self):
        """Test mock analysis with positive text."""
        analyzer = SentimentAnalyzer()
        
        result = analyzer._mock_analyze("Bu çok güzel ve harika bir haber!")
        
        assert 'score' in result
        assert 'magnitude' in result
        assert 'label' in result
        assert result['score'] > 0
    
    def test_mock_analyze_negative(self):
        """Test mock analysis with negative text."""
        analyzer = SentimentAnalyzer()
        
        result = analyzer._mock_analyze("Bu çok kötü ve korkunç bir durum.")
        
        assert result['score'] < 0
    
    def test_mock_analyze_neutral(self):
        """Test mock analysis with neutral text."""
        analyzer = SentimentAnalyzer()
        
        result = analyzer._mock_analyze("Bugün hava bulutlu.")
        
        assert result['label'] == "neutral"


class TestAnalyzeMethod:
    """Tests for the analyze method."""
    
    def test_analyze_empty_text(self):
        """Test error with empty text."""
        analyzer = SentimentAnalyzer()
        
        with pytest.raises(EmptyTextError):
            analyzer.analyze("")
    
    def test_analyze_whitespace_only(self):
        """Test error with whitespace-only text."""
        analyzer = SentimentAnalyzer()
        
        with pytest.raises(EmptyTextError):
            analyzer.analyze("   ")
    
    def test_analyze_too_long_text(self):
        """Test error with too long text."""
        analyzer = SentimentAnalyzer()
        
        long_text = "a" * 6000
        
        with pytest.raises(TextTooLongError):
            analyzer.analyze(long_text)
    
    def test_analyze_valid_text(self):
        """Test analysis with valid text."""
        analyzer = SentimentAnalyzer()
        
        result = analyzer.analyze("İklim değişikliği önemli bir konu.")
        
        assert 'score' in result
        assert 'magnitude' in result
        assert 'label' in result
        assert isinstance(result['score'], float)
        assert -1 <= result['score'] <= 1


class TestBatchAnalysis:
    """Tests for batch analysis."""
    
    def test_analyze_batch(self):
        """Test batch analysis."""
        analyzer = SentimentAnalyzer()
        
        texts = [
            "Bu güzel bir haber.",
            "Bu kötü bir durum.",
            "Bugün pazartesi.",
        ]
        
        results = analyzer.analyze_batch(texts, show_progress=False)
        
        assert len(results) == 3
        assert all(r is not None for r in results)
    
    def test_analyze_batch_with_empty(self):
        """Test batch analysis with empty texts."""
        analyzer = SentimentAnalyzer()
        
        texts = [
            "Güzel haber.",
            "",  # Empty
            "Normal metin.",
        ]
        
        results = analyzer.analyze_batch(texts, show_progress=False)
        
        assert len(results) == 3
        assert results[0] is not None
        assert results[1] is None  # Empty text
        assert results[2] is not None


class TestDataFrameAnalysis:
    """Tests for DataFrame analysis."""
    
    def test_analyze_dataframe(self, cleaned_dataframe):
        """Test DataFrame analysis."""
        analyzer = SentimentAnalyzer()
        
        result = analyzer.analyze_dataframe(cleaned_dataframe)
        
        assert 'sentiment_score' in result.columns
        assert 'sentiment_magnitude' in result.columns
        assert 'sentiment_label' in result.columns
    
    def test_analyze_dataframe_missing_column(self):
        """Test error with missing text column."""
        analyzer = SentimentAnalyzer()
        
        df = pd.DataFrame({'id': [1], 'author': ['user']})
        
        with pytest.raises(ValueError):
            analyzer.analyze_dataframe(df)


class TestSentimentSummary:
    """Tests for sentiment summary function."""
    
    def test_get_sentiment_summary(self, analyzed_dataframe):
        """Test sentiment summary calculation."""
        summary = get_sentiment_summary(analyzed_dataframe)
        
        assert 'total_posts' in summary
        assert 'analyzed_posts' in summary
        assert 'positive_count' in summary
        assert 'negative_count' in summary
        assert 'neutral_count' in summary
        assert 'positive_percentage' in summary
        assert 'average_score' in summary
    
    def test_get_sentiment_summary_missing_column(self):
        """Test error with missing sentiment column."""
        df = pd.DataFrame({'id': [1], 'text': ['hello']})
        
        with pytest.raises(ValueError):
            get_sentiment_summary(df)


class TestThresholds:
    """Tests for sentiment thresholds."""
    
    def test_positive_threshold(self):
        """Test positive threshold value."""
        assert POSITIVE_THRESHOLD == 0.25
    
    def test_negative_threshold(self):
        """Test negative threshold value."""
        assert NEGATIVE_THRESHOLD == -0.25


