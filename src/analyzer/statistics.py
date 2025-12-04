"""
Statistical analysis module for DataScope.

This module provides statistical analysis functions for the collected
and analyzed data.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter

import pandas as pd
import numpy as np

from ..utils.logger import get_logger

logger = get_logger(__name__)


def calculate_basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate basic statistics for the dataset.
    
    Args:
        df: DataFrame with post data
        
    Returns:
        Dict: Basic statistics including:
            - total_posts: Total number of posts
            - unique_authors: Number of unique authors
            - date_range: (min_date, max_date) tuple
            - avg_text_length: Average text length
    """
    stats = {
        "total_posts": len(df),
        "unique_authors": df['author'].nunique() if 'author' in df.columns else 0,
        "avg_text_length": df['text_length'].mean() if 'text_length' in df.columns else 0,
        "max_text_length": df['text_length'].max() if 'text_length' in df.columns else 0,
        "min_text_length": df['text_length'].min() if 'text_length' in df.columns else 0,
    }
    
    # Date range
    if 'created_at' in df.columns:
        try:
            dates = pd.to_datetime(df['created_at'])
            stats["date_range"] = {
                "start": dates.min().isoformat() if pd.notna(dates.min()) else None,
                "end": dates.max().isoformat() if pd.notna(dates.max()) else None,
                "span_days": (dates.max() - dates.min()).days if pd.notna(dates.min()) else 0,
            }
        except Exception:
            stats["date_range"] = None
    
    return stats


def calculate_engagement_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate engagement statistics.
    
    Args:
        df: DataFrame with engagement columns
        
    Returns:
        Dict: Engagement statistics
    """
    count_cols = ['reblogs_count', 'favourites_count', 'replies_count']
    existing_cols = [col for col in count_cols if col in df.columns]
    
    if not existing_cols:
        return {"error": "No engagement columns found"}
    
    stats = {}
    
    for col in existing_cols:
        col_data = df[col]
        stats[col] = {
            "total": int(col_data.sum()),
            "mean": round(float(col_data.mean()), 2),
            "median": round(float(col_data.median()), 2),
            "max": int(col_data.max()),
            "std": round(float(col_data.std()), 2),
        }
    
    # Total engagement
    if existing_cols:
        total_engagement = df[existing_cols].sum(axis=1)
        stats["total_engagement"] = {
            "sum": int(total_engagement.sum()),
            "mean": round(float(total_engagement.mean()), 2),
            "median": round(float(total_engagement.median()), 2),
            "max": int(total_engagement.max()),
        }
    
    return stats


def calculate_temporal_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate temporal statistics (posts over time).
    
    Args:
        df: DataFrame with created_at column
        
    Returns:
        Dict: Temporal statistics
    """
    if 'created_at' not in df.columns:
        return {"error": "No created_at column found"}
    
    df = df.copy()
    
    try:
        # Use ISO8601 format to handle various datetime formats including microseconds
        df['created_at'] = pd.to_datetime(df['created_at'], format='ISO8601', utc=True)
    except Exception as e:
        return {"error": f"Could not parse dates: {e}"}
    
    # Posts by date
    df['date'] = df['created_at'].dt.date
    posts_by_date = df.groupby('date').size().to_dict()
    
    # Posts by hour
    df['hour'] = df['created_at'].dt.hour
    posts_by_hour = df.groupby('hour').size().to_dict()
    
    # Posts by day of week (0=Monday, 6=Sunday)
    df['day_of_week'] = df['created_at'].dt.dayofweek
    posts_by_dow = df.groupby('day_of_week').size().to_dict()
    
    # Peak times
    peak_hour = max(posts_by_hour, key=posts_by_hour.get) if posts_by_hour else None
    peak_day = max(posts_by_dow, key=posts_by_dow.get) if posts_by_dow else None
    
    day_names = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
    
    return {
        "posts_by_date": {str(k): v for k, v in posts_by_date.items()},
        "posts_by_hour": posts_by_hour,
        "posts_by_day_of_week": posts_by_dow,
        "peak_hour": peak_hour,
        "peak_day": day_names[peak_day] if peak_day is not None else None,
        "avg_posts_per_day": round(len(df) / len(posts_by_date), 2) if posts_by_date else 0,
    }


def calculate_author_stats(df: pd.DataFrame, top_n: int = 10) -> Dict[str, Any]:
    """
    Calculate author-related statistics.
    
    Args:
        df: DataFrame with author column
        top_n: Number of top authors to return
        
    Returns:
        Dict: Author statistics
    """
    if 'author' not in df.columns:
        return {"error": "No author column found"}
    
    # Posts per author
    posts_per_author = df['author'].value_counts()
    
    # Top authors
    top_authors = posts_per_author.head(top_n).to_dict()
    
    # Author engagement if available
    engagement_cols = ['reblogs_count', 'favourites_count', 'replies_count']
    existing_cols = [col for col in engagement_cols if col in df.columns]
    
    top_authors_by_engagement = {}
    if existing_cols:
        df['total_engagement'] = df[existing_cols].sum(axis=1)
        engagement_by_author = df.groupby('author')['total_engagement'].sum()
        top_authors_by_engagement = engagement_by_author.nlargest(top_n).to_dict()
    
    return {
        "unique_authors": int(df['author'].nunique()),
        "top_authors_by_posts": top_authors,
        "top_authors_by_engagement": top_authors_by_engagement,
        "avg_posts_per_author": round(len(df) / df['author'].nunique(), 2),
        "authors_with_single_post": int((posts_per_author == 1).sum()),
    }


def calculate_sentiment_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate detailed sentiment statistics.
    
    Args:
        df: DataFrame with sentiment columns
        
    Returns:
        Dict: Sentiment statistics
    """
    if 'sentiment_label' not in df.columns:
        return {"error": "No sentiment_label column found"}
    
    # Basic counts
    label_counts = df['sentiment_label'].value_counts().to_dict()
    total_analyzed = df['sentiment_label'].notna().sum()
    
    stats = {
        "total_analyzed": int(total_analyzed),
        "positive_count": int(label_counts.get('positive', 0)),
        "negative_count": int(label_counts.get('negative', 0)),
        "neutral_count": int(label_counts.get('neutral', 0)),
    }
    
    # Percentages
    if total_analyzed > 0:
        stats["positive_percentage"] = round(stats["positive_count"] / total_analyzed * 100, 2)
        stats["negative_percentage"] = round(stats["negative_count"] / total_analyzed * 100, 2)
        stats["neutral_percentage"] = round(stats["neutral_count"] / total_analyzed * 100, 2)
    
    # Score statistics
    if 'sentiment_score' in df.columns:
        scores = df['sentiment_score'].dropna()
        stats["score_stats"] = {
            "mean": round(float(scores.mean()), 4),
            "median": round(float(scores.median()), 4),
            "std": round(float(scores.std()), 4),
            "min": round(float(scores.min()), 4),
            "max": round(float(scores.max()), 4),
        }
    
    # Magnitude statistics
    if 'sentiment_magnitude' in df.columns:
        magnitudes = df['sentiment_magnitude'].dropna()
        stats["magnitude_stats"] = {
            "mean": round(float(magnitudes.mean()), 4),
            "median": round(float(magnitudes.median()), 4),
            "max": round(float(magnitudes.max()), 4),
        }
    
    return stats


def calculate_sentiment_by_time(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate sentiment trends over time.
    
    Args:
        df: DataFrame with sentiment and date columns
        
    Returns:
        Dict: Sentiment by time periods
    """
    required_cols = ['sentiment_score', 'created_at']
    if not all(col in df.columns for col in required_cols):
        return {"error": "Required columns not found"}
    
    df = df.copy()
    # Use ISO8601 format to handle various datetime formats including microseconds
    df['created_at'] = pd.to_datetime(df['created_at'], format='ISO8601', utc=True)
    df['date'] = df['created_at'].dt.date
    
    # Daily sentiment
    daily_sentiment = df.groupby('date').agg({
        'sentiment_score': ['mean', 'count']
    }).round(4)
    
    daily_sentiment.columns = ['avg_score', 'count']
    daily_sentiment = daily_sentiment.reset_index()
    
    return {
        "daily_sentiment": [
            {
                "date": str(row['date']),
                "avg_score": float(row['avg_score']) if pd.notna(row['avg_score']) else None,
                "count": int(row['count']),
            }
            for _, row in daily_sentiment.iterrows()
        ],
    }


def calculate_word_stats(
    df: pd.DataFrame, 
    text_column: str = 'cleaned_text',
    top_n: int = 50
) -> Dict[str, Any]:
    """
    Calculate word frequency statistics.
    
    Args:
        df: DataFrame with text column
        text_column: Name of the text column
        top_n: Number of top words to return
        
    Returns:
        Dict: Word statistics
    """
    if text_column not in df.columns:
        return {"error": f"Column '{text_column}' not found"}
    
    from ..processor.cleaning import get_word_frequencies, TURKISH_STOPWORDS
    
    texts = df[text_column].fillna('').tolist()
    word_freqs = get_word_frequencies(texts, stopwords=TURKISH_STOPWORDS)
    
    # Get top words
    top_words = dict(list(word_freqs.items())[:top_n])
    
    # Total unique words
    total_unique = len(word_freqs)
    
    # Total words
    total_words = sum(word_freqs.values())
    
    return {
        "top_words": top_words,
        "total_unique_words": total_unique,
        "total_words": total_words,
        "avg_words_per_post": round(total_words / len(df), 2) if len(df) > 0 else 0,
    }


def generate_full_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical report.
    
    Args:
        df: DataFrame with all available columns
        
    Returns:
        Dict: Complete statistical report
    """
    logger.info("Generating full statistical report...")
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "basic_stats": calculate_basic_stats(df),
        "engagement_stats": calculate_engagement_stats(df),
        "temporal_stats": calculate_temporal_stats(df),
        "author_stats": calculate_author_stats(df),
    }
    
    # Add sentiment stats if available
    if 'sentiment_label' in df.columns:
        report["sentiment_stats"] = calculate_sentiment_stats(df)
        report["sentiment_by_time"] = calculate_sentiment_by_time(df)
    
    # Add word stats
    if 'cleaned_text' in df.columns:
        report["word_stats"] = calculate_word_stats(df)
    
    logger.info("Statistical report generated")
    
    return report


