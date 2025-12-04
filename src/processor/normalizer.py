"""
Data normalization module for DataScope.

This module provides functions for normalizing and standardizing data
after cleaning, preparing it for analysis.
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

from ..utils.logger import get_logger

logger = get_logger(__name__)


def normalize_dates(df: pd.DataFrame, date_column: str = 'created_at') -> pd.DataFrame:
    """
    Normalize date column to datetime objects.
    
    Args:
        df: DataFrame with date column
        date_column: Name of the date column (default: 'created_at')
        
    Returns:
        pd.DataFrame: DataFrame with normalized dates
    """
    df = df.copy()
    
    if date_column not in df.columns:
        logger.warning(f"Date column '{date_column}' not found")
        return df
    
    # Try to parse dates using ISO8601 format to handle various formats including microseconds
    try:
        df[date_column] = pd.to_datetime(df[date_column], format='ISO8601', utc=True)
        
        # Extract additional date features
        df['date'] = df[date_column].dt.date
        df['hour'] = df[date_column].dt.hour
        df['day_of_week'] = df[date_column].dt.dayofweek
        df['week'] = df[date_column].dt.isocalendar().week
        
        logger.info(f"Date normalization complete for column '{date_column}'")
        
    except Exception as e:
        logger.warning(f"Could not parse dates in column '{date_column}': {e}")
    
    return df


def normalize_counts(df: pd.DataFrame, count_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Normalize count columns (ensure they are integers and non-negative).
    
    Args:
        df: DataFrame with count columns
        count_columns: List of count column names
        
    Returns:
        pd.DataFrame: DataFrame with normalized counts
    """
    df = df.copy()
    
    if count_columns is None:
        count_columns = ['reblogs_count', 'favourites_count', 'replies_count']
    
    for col in count_columns:
        if col in df.columns:
            # Convert to numeric, filling NaN with 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            # Ensure non-negative
            df[col] = df[col].clip(lower=0)
    
    logger.debug(f"Normalized count columns: {count_columns}")
    
    return df


def normalize_authors(df: pd.DataFrame, author_column: str = 'author') -> pd.DataFrame:
    """
    Normalize author names (lowercase, strip whitespace).
    
    Args:
        df: DataFrame with author column
        author_column: Name of the author column (default: 'author')
        
    Returns:
        pd.DataFrame: DataFrame with normalized author names
    """
    df = df.copy()
    
    if author_column not in df.columns:
        logger.warning(f"Author column '{author_column}' not found")
        return df
    
    # Strip whitespace and lowercase
    df[author_column] = df[author_column].str.strip().str.lower()
    
    logger.debug(f"Normalized author column '{author_column}'")
    
    return df


def normalize_text_encoding(text: str) -> str:
    """
    Normalize text encoding (fix common encoding issues).
    
    Args:
        text: Text with potential encoding issues
        
    Returns:
        str: Text with normalized encoding
    """
    if not text:
        return ""
    
    # Common replacements for encoding issues
    replacements = {
        'â€™': "'",
        'â€œ': '"',
        'â€': '"',
        'â€"': '–',
        'â€"': '—',
        'Ã¼': 'ü',
        'Ã¶': 'ö',
        'Ã§': 'ç',
        'ÄŸ': 'ğ',
        'Ä±': 'ı',
        'ÅŸ': 'ş',
        'Ã‡': 'Ç',
        'Ä°': 'İ',
        'Ãœ': 'Ü',
        'Ã–': 'Ö',
        'Åž': 'Ş',
        'Ä': 'Ğ',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def calculate_engagement_score(row: pd.Series) -> float:
    """
    Calculate an engagement score for a post.
    
    Score is based on reblogs, favourites, and replies with different weights.
    
    Args:
        row: DataFrame row with count columns
        
    Returns:
        float: Engagement score
    """
    reblogs = row.get('reblogs_count', 0)
    favourites = row.get('favourites_count', 0)
    replies = row.get('replies_count', 0)
    
    # Weighted sum (reblogs are most valuable, then favourites, then replies)
    score = (reblogs * 3) + (favourites * 2) + (replies * 1)
    
    return float(score)


def add_engagement_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add engagement metrics to DataFrame.
    
    Adds columns:
    - engagement_score: Weighted sum of interactions
    - total_interactions: Sum of all interactions
    - engagement_level: Categorical (low/medium/high)
    
    Args:
        df: DataFrame with count columns
        
    Returns:
        pd.DataFrame: DataFrame with engagement metrics
    """
    df = df.copy()
    
    # Calculate engagement score
    df['engagement_score'] = df.apply(calculate_engagement_score, axis=1)
    
    # Total interactions
    count_cols = ['reblogs_count', 'favourites_count', 'replies_count']
    existing_cols = [col for col in count_cols if col in df.columns]
    
    if existing_cols:
        df['total_interactions'] = df[existing_cols].sum(axis=1)
    else:
        df['total_interactions'] = 0
    
    # Engagement level based on percentiles
    # Check if there's enough variation in the data
    unique_scores = df['engagement_score'].nunique()
    
    if unique_scores <= 1:
        # All values are the same, assign default level
        df['engagement_level'] = 'low'
        logger.debug("All engagement scores are identical, defaulting to 'low'")
    elif df['engagement_score'].sum() == 0:
        # All zeros
        df['engagement_level'] = 'low'
        logger.debug("All engagement scores are zero, defaulting to 'low'")
    else:
        try:
            # Calculate quantiles
            q33 = df['engagement_score'].quantile(0.33)
            q66 = df['engagement_score'].quantile(0.66)
            
            # Use duplicates='drop' to handle cases where quantiles are equal
            df['engagement_level'] = pd.cut(
                df['engagement_score'],
                bins=[-np.inf, q33, q66, np.inf],
                labels=['low', 'medium', 'high'],
                duplicates='drop'
            )
        except ValueError:
            # Fallback: use simple threshold-based categorization
            median_score = df['engagement_score'].median()
            df['engagement_level'] = df['engagement_score'].apply(
                lambda x: 'high' if x > median_score else ('medium' if x > 0 else 'low')
            )
    
    logger.debug("Added engagement metrics")
    
    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all normalization steps to a DataFrame.
    
    Args:
        df: Raw or cleaned DataFrame
        
    Returns:
        pd.DataFrame: Fully normalized DataFrame
    """
    logger.info(f"Normalizing {len(df)} posts...")
    
    # Apply normalization steps
    df = normalize_dates(df)
    df = normalize_counts(df)
    df = normalize_authors(df)
    df = add_engagement_metrics(df)
    
    logger.info("Normalization complete")
    
    return df


def filter_by_date_range(
    df: pd.DataFrame, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    date_column: str = 'created_at'
) -> pd.DataFrame:
    """
    Filter DataFrame by date range.
    
    Args:
        df: DataFrame with date column
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        date_column: Name of date column
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    df = df.copy()
    
    if date_column not in df.columns:
        logger.warning(f"Date column '{date_column}' not found")
        return df
    
    # Ensure datetime type
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column], format='ISO8601', utc=True)
    
    # Apply filters
    if start_date:
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=df[date_column].dt.tz)
        df = df[df[date_column] >= start_date]
    
    if end_date:
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=df[date_column].dt.tz)
        df = df[df[date_column] <= end_date]
    
    logger.debug(f"Filtered to {len(df)} posts in date range")
    
    return df


def filter_by_language(df: pd.DataFrame, language: str = 'tr') -> pd.DataFrame:
    """
    Filter DataFrame by language.
    
    Args:
        df: DataFrame with language column
        language: Language code to filter by (default: 'tr' for Turkish)
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    if 'language' not in df.columns:
        logger.warning("Language column not found")
        return df
    
    filtered = df[df['language'] == language].copy()
    
    logger.debug(f"Filtered to {len(filtered)} posts with language '{language}'")
    
    return filtered


def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove duplicate posts from DataFrame.
    
    Args:
        df: DataFrame with potential duplicates
        subset: Columns to consider for duplicates (default: ['id'])
        
    Returns:
        pd.DataFrame: DataFrame without duplicates
    """
    original_count = len(df)
    
    if subset is None:
        subset = ['id']
    
    df = df.drop_duplicates(subset=subset, keep='first')
    
    removed_count = original_count - len(df)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} duplicate posts")
    
    return df

