"""
Pytest configuration and fixtures for DataScope tests.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_posts():
    """Create sample post data for testing."""
    base_date = datetime.now()
    
    posts = [
        {
            'id': '1',
            'text': '<p>İklim değişikliği çok önemli bir konu. #iklim</p>',
            'author': 'user1',
            'created_at': (base_date - timedelta(days=1)).isoformat(),
            'reblogs_count': 5,
            'favourites_count': 10,
            'replies_count': 2,
            'instance': 'https://mastodon.social',
        },
        {
            'id': '2',
            'text': '<p>Yenilenebilir enerji kaynaklarına yatırım artmalı. @someone</p>',
            'author': 'user2',
            'created_at': (base_date - timedelta(days=2)).isoformat(),
            'reblogs_count': 3,
            'favourites_count': 8,
            'replies_count': 1,
            'instance': 'https://mastodon.social',
        },
        {
            'id': '3',
            'text': '<p>Çevre kirliliği geleceğimizi tehdit ediyor. https://example.com</p>',
            'author': 'user3',
            'created_at': base_date.isoformat(),
            'reblogs_count': 10,
            'favourites_count': 25,
            'replies_count': 5,
            'instance': 'https://mastodon.social',
        },
    ]
    
    return posts


@pytest.fixture
def sample_dataframe(sample_posts):
    """Create sample DataFrame for testing."""
    return pd.DataFrame(sample_posts)


@pytest.fixture
def cleaned_dataframe(sample_dataframe):
    """Create cleaned DataFrame for testing."""
    from src.processor import process_dataframe
    return process_dataframe(sample_dataframe)


@pytest.fixture
def analyzed_dataframe(cleaned_dataframe):
    """Create analyzed DataFrame with sentiment columns."""
    df = cleaned_dataframe.copy()
    
    # Add mock sentiment data
    df['sentiment_score'] = [0.5, -0.3, 0.1]
    df['sentiment_magnitude'] = [0.8, 0.6, 0.4]
    df['sentiment_label'] = ['positive', 'negative', 'neutral']
    
    return df


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_mastodon_response():
    """Create mock Mastodon API response."""
    return [
        {
            'id': 12345,
            'content': '<p>Test post about climate #iklim</p>',
            'account': {
                'acct': 'testuser',
                'username': 'testuser',
            },
            'created_at': datetime.now(),
            'reblogs_count': 5,
            'favourites_count': 10,
            'replies_count': 2,
            'url': 'https://mastodon.social/@testuser/12345',
            'language': 'tr',
            'visibility': 'public',
        },
    ]


@pytest.fixture(autouse=True)
def reset_config():
    """Reset configuration before each test."""
    from src.utils.config import reset_config
    reset_config()
    yield
    reset_config()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv('MASTODON_INSTANCE', 'https://mastodon.social')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
    monkeypatch.setenv('OUTPUT_DIR', '/tmp/ika-vms-test/outputs')
    monkeypatch.setenv('DATA_DIR', '/tmp/ika-vms-test/data')
    monkeypatch.setenv('LOG_DIR', '/tmp/ika-vms-test/logs')


