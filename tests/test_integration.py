"""
Integration tests for DataScope.

These tests verify that the different modules work together correctly.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, Mock

from src.scraper import MastodonScraper
from src.processor import process_dataframe, normalize_dataframe
from src.analyzer import SentimentAnalyzer, generate_full_report
from src.output import (
    create_all_visualizations,
    save_analysis_results,
    create_sample_data,
)


class TestFullPipeline:
    """Integration tests for the full analysis pipeline."""
    
    def test_sample_data_pipeline(self, temp_output_dir):
        """Test full pipeline with sample data."""
        # Step 1: Create sample data
        df = create_sample_data(num_posts=10)
        
        assert len(df) == 10
        assert 'text' in df.columns
        assert 'author' in df.columns
        
        # Step 2: Process data
        df = process_dataframe(df)
        
        assert 'cleaned_text' in df.columns
        assert 'text_length' in df.columns
        
        # Step 3: Normalize data
        df = normalize_dataframe(df)
        
        assert 'date' in df.columns or 'created_at' in df.columns
        
        # Step 4: Sentiment analysis (mock mode)
        analyzer = SentimentAnalyzer()
        df = analyzer.analyze_dataframe(df)
        
        assert 'sentiment_score' in df.columns
        assert 'sentiment_label' in df.columns
        
        # Step 5: Generate statistics
        stats = generate_full_report(df)
        
        assert 'basic_stats' in stats
        assert 'sentiment_stats' in stats
        
        # Step 6: Save results
        saved = save_analysis_results(df, stats, temp_output_dir)
        
        assert len(saved) > 0
        assert any('csv' in k for k in saved.keys())
    
    def test_visualization_pipeline(self, analyzed_dataframe, temp_output_dir):
        """Test visualization creation with analyzed data."""
        # Create visualizations
        graphs = create_all_visualizations(analyzed_dataframe, temp_output_dir)
        
        # Should create at least sentiment distribution
        assert len(graphs) > 0
        
        # Check files exist
        for name, path in graphs.items():
            assert Path(path).exists(), f"File not found: {path}"
    
    @patch('src.scraper.mastodon.Mastodon')
    def test_scraper_to_analysis_pipeline(
        self, 
        mock_mastodon, 
        mock_mastodon_response,
        temp_output_dir
    ):
        """Test pipeline from scraping to analysis."""
        # Setup mock
        mock_client = Mock()
        mock_client.instance.return_value = {'title': 'Test'}
        mock_client.timeline_hashtag.return_value = mock_mastodon_response
        mock_mastodon.return_value = mock_client
        
        # Step 1: Scrape
        scraper = MastodonScraper("https://mastodon.social")
        posts = scraper.fetch_by_hashtag("test", limit=5)
        
        assert len(posts) > 0
        
        # Step 2: Convert to DataFrame
        df = pd.DataFrame(posts)
        
        assert 'text' in df.columns
        
        # Step 3: Process
        df = process_dataframe(df)
        
        assert 'cleaned_text' in df.columns
        
        # Step 4: Analyze
        analyzer = SentimentAnalyzer()
        df = analyzer.analyze_dataframe(df)
        
        assert 'sentiment_label' in df.columns
        
        # Step 5: Generate report
        stats = generate_full_report(df)
        
        assert stats['basic_stats']['total_posts'] > 0


class TestDataFlow:
    """Tests for data flow between modules."""
    
    def test_cleaning_preserves_rows(self, sample_dataframe):
        """Test that cleaning doesn't lose rows."""
        original_count = len(sample_dataframe)
        
        cleaned = process_dataframe(sample_dataframe)
        
        assert len(cleaned) == original_count
    
    def test_normalization_adds_columns(self, cleaned_dataframe):
        """Test that normalization adds expected columns."""
        normalized = normalize_dataframe(cleaned_dataframe)
        
        # Should have engagement metrics
        assert 'engagement_score' in normalized.columns
        assert 'total_interactions' in normalized.columns
    
    def test_statistics_generation(self, analyzed_dataframe):
        """Test statistics generation from analyzed data."""
        stats = generate_full_report(analyzed_dataframe)
        
        # Basic stats
        assert stats['basic_stats']['total_posts'] == len(analyzed_dataframe)
        
        # Sentiment stats
        sentiment = stats.get('sentiment_stats', {})
        assert sentiment['total_analyzed'] > 0
        
        # Percentages should sum to ~100
        total_pct = (
            sentiment.get('positive_percentage', 0) +
            sentiment.get('negative_percentage', 0) +
            sentiment.get('neutral_percentage', 0)
        )
        assert 99 <= total_pct <= 101


class TestErrorHandling:
    """Tests for error handling across modules."""
    
    def test_invalid_dataframe_handling(self):
        """Test handling of invalid DataFrames."""
        from src.utils.exceptions import MissingColumnError
        
        invalid_df = pd.DataFrame({'invalid': [1, 2, 3]})
        
        with pytest.raises(MissingColumnError):
            process_dataframe(invalid_df)
    
    def test_empty_dataframe_handling(self, temp_output_dir):
        """Test handling of empty DataFrames."""
        empty_df = pd.DataFrame(columns=['id', 'text', 'author', 'created_at'])
        
        # Should handle empty DataFrame gracefully
        processed = process_dataframe(empty_df)
        assert len(processed) == 0
        
        # Statistics should handle empty data
        stats = generate_full_report(processed)
        assert stats['basic_stats']['total_posts'] == 0


class TestOutputConsistency:
    """Tests for output consistency."""
    
    def test_csv_roundtrip(self, analyzed_dataframe, temp_output_dir):
        """Test CSV save and load."""
        from src.output import save_to_csv, load_from_csv
        
        path = Path(temp_output_dir) / "test.csv"
        
        # Save
        save_to_csv(analyzed_dataframe, str(path))
        
        # Load
        loaded = load_from_csv(str(path))
        
        # Compare (note: some type conversion may occur)
        assert len(loaded) == len(analyzed_dataframe)
        assert set(loaded.columns) == set(analyzed_dataframe.columns)
    
    def test_json_roundtrip(self, temp_output_dir):
        """Test JSON save and load."""
        from src.output import save_to_json, load_from_json
        
        data = {'key': 'value', 'number': 42, 'list': [1, 2, 3]}
        path = Path(temp_output_dir) / "test.json"
        
        # Save
        save_to_json(data, str(path))
        
        # Load
        loaded = load_from_json(str(path))
        
        assert loaded == data


