"""
Data validation module for DataScope.

This module provides quality scoring and automatic filtering for collected data.
It helps identify problematic posts before analysis.
"""

import re
from typing import Dict, List, Tuple, Optional, Set
from collections import Counter
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Quality score thresholds
QUALITY_HIGH = 70
QUALITY_MEDIUM = 40
QUALITY_LOW = 0

# Spam keywords (Turkish)
SPAM_KEYWORDS = {
    'satılık', 'kiralık', 'indirim', 'kampanya', 'fırsat', 'ücretsiz',
    'kazanç', 'gelir', 'para kazan', 'hemen tıkla', 'link bio',
    'takip et', 'follow', 'dm', 'reklam', 'sponsor', 'promosyon',
    'satış', 'sipariş', 'whatsapp', 'telegram grubu', 'özel teklif',
}

# Bot detection patterns
BOT_PATTERNS = [
    r'^RT\s',  # Retweet pattern
    r'^\[BOT\]',  # Bot indicator
    r'#\w+\s*' * 5,  # Too many hashtags (5+)
]


class DataValidator:
    """
    Validates and scores data quality for scientific research.
    
    This class provides methods to:
    - Calculate quality scores for each post
    - Detect spam, bots, and low-quality content
    - Filter data based on various criteria
    
    Example:
        >>> validator = DataValidator()
        >>> df = validator.validate_dataframe(raw_df)
        >>> clean_df = validator.filter_by_quality(df, min_score=50)
    """
    
    def __init__(
        self,
        min_text_length: int = 10,
        max_url_count: int = 2,
        suspicious_post_threshold: int = 50,
    ):
        """
        Initialize the validator.
        
        Args:
            min_text_length: Minimum text length for valid posts
            max_url_count: Maximum allowed URLs in a post
            suspicious_post_threshold: Posts per day to flag as suspicious
        """
        self.min_text_length = min_text_length
        self.max_url_count = max_url_count
        self.suspicious_post_threshold = suspicious_post_threshold
        
        # Compile regex patterns
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F'  # Emoticons
            r'\U0001F300-\U0001F5FF'  # Symbols & pictographs
            r'\U0001F680-\U0001F6FF'  # Transport & map symbols
            r'\U0001F1E0-\U0001F1FF'  # Flags
            r'\U00002702-\U000027B0'  # Dingbats
            r'\U0001F900-\U0001F9FF'  # Supplemental symbols
            r']+', re.UNICODE
        )
        self.hashtag_pattern = re.compile(r'#\w+')
        self.bot_patterns = [re.compile(p, re.IGNORECASE) for p in BOT_PATTERNS]
    
    def calculate_quality_score(self, row: pd.Series) -> Dict:
        """
        Calculate quality score for a single post.
        
        Args:
            row: DataFrame row containing post data
            
        Returns:
            Dict with score and issue details
        """
        score = 100
        issues = []
        
        text = str(row.get('cleaned_text', row.get('text', '')))
        
        # 1. Text length check (-30)
        if len(text) < self.min_text_length:
            score -= 30
            issues.append('too_short')
        
        # 2. Only emoji/symbols check (-50)
        text_without_emoji = self.emoji_pattern.sub('', text)
        text_without_emoji = re.sub(r'[^\w\s]', '', text_without_emoji)
        if len(text_without_emoji.strip()) < 5:
            score -= 50
            issues.append('emoji_only')
        
        # 3. URL count check (-20)
        url_count = len(self.url_pattern.findall(str(row.get('text', ''))))
        if url_count > self.max_url_count:
            score -= 20
            issues.append('too_many_urls')
        
        # 4. Hashtag spam check (-15)
        hashtag_count = len(self.hashtag_pattern.findall(str(row.get('text', ''))))
        if hashtag_count > 5:
            score -= 15
            issues.append('hashtag_spam')
        
        # 5. Spam keywords check (-35)
        text_lower = text.lower()
        spam_found = [kw for kw in SPAM_KEYWORDS if kw in text_lower]
        if spam_found:
            score -= 35
            issues.append('spam_keywords')
        
        # 6. Bot pattern check (-25)
        for pattern in self.bot_patterns:
            if pattern.search(text):
                score -= 25
                issues.append('bot_pattern')
                break
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        return {
            'quality_score': score,
            'quality_issues': issues,
            'quality_level': self._score_to_level(score)
        }
    
    def _score_to_level(self, score: int) -> str:
        """Convert score to quality level."""
        if score >= QUALITY_HIGH:
            return 'high'
        elif score >= QUALITY_MEDIUM:
            return 'medium'
        else:
            return 'low'
    
    def detect_duplicates(self, df: pd.DataFrame, text_column: str = 'cleaned_text') -> pd.Series:
        """
        Detect duplicate or near-duplicate content.
        
        Args:
            df: DataFrame to check
            text_column: Column containing text
            
        Returns:
            pd.Series: Boolean series marking duplicates
        """
        if text_column not in df.columns:
            text_column = 'text'
        
        # Exact duplicates
        is_duplicate = df[text_column].duplicated(keep='first')
        
        return is_duplicate
    
    def detect_suspicious_authors(self, df: pd.DataFrame) -> Set[str]:
        """
        Detect authors with suspiciously high posting frequency.
        
        Args:
            df: DataFrame with author and date columns
            
        Returns:
            Set of suspicious author names
        """
        suspicious = set()
        
        if 'author' not in df.columns:
            return suspicious
        
        # Count posts per author
        author_counts = df['author'].value_counts()
        
        # Flag authors with too many posts
        for author, count in author_counts.items():
            if count > self.suspicious_post_threshold:
                suspicious.add(author)
        
        return suspicious
    
    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate entire DataFrame and add quality columns.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            DataFrame with quality columns added:
            - quality_score: 0-100 score
            - quality_level: 'high', 'medium', 'low'
            - quality_issues: List of detected issues
            - is_duplicate: Boolean
            - is_suspicious_author: Boolean
        """
        df = df.copy()
        
        logger.info(f"Validating {len(df)} posts...")
        
        # Calculate quality scores
        quality_data = df.apply(self.calculate_quality_score, axis=1)
        
        df['quality_score'] = quality_data.apply(lambda x: x['quality_score'])
        df['quality_level'] = quality_data.apply(lambda x: x['quality_level'])
        df['quality_issues'] = quality_data.apply(lambda x: x['quality_issues'])
        
        # Detect duplicates
        df['is_duplicate'] = self.detect_duplicates(df)
        
        # Apply duplicate penalty to score
        df.loc[df['is_duplicate'], 'quality_score'] = df.loc[df['is_duplicate'], 'quality_score'] - 40
        df.loc[df['is_duplicate'], 'quality_issues'] = df.loc[df['is_duplicate'], 'quality_issues'].apply(
            lambda x: x + ['duplicate'] if 'duplicate' not in x else x
        )
        
        # Detect suspicious authors
        suspicious_authors = self.detect_suspicious_authors(df)
        df['is_suspicious_author'] = df['author'].isin(suspicious_authors)
        
        # Apply suspicious author penalty
        df.loc[df['is_suspicious_author'], 'quality_score'] = df.loc[df['is_suspicious_author'], 'quality_score'] - 25
        df.loc[df['is_suspicious_author'], 'quality_issues'] = df.loc[df['is_suspicious_author'], 'quality_issues'].apply(
            lambda x: x + ['suspicious_author'] if 'suspicious_author' not in x else x
        )
        
        # Ensure score bounds
        df['quality_score'] = df['quality_score'].clip(0, 100)
        
        # Update quality levels
        df['quality_level'] = df['quality_score'].apply(self._score_to_level)
        
        # Add validation status
        df['is_valid'] = df['quality_score'] >= QUALITY_MEDIUM
        
        logger.info(f"Validation complete. High: {(df['quality_level'] == 'high').sum()}, "
                   f"Medium: {(df['quality_level'] == 'medium').sum()}, "
                   f"Low: {(df['quality_level'] == 'low').sum()}")
        
        return df
    
    def filter_by_quality(
        self, 
        df: pd.DataFrame, 
        min_score: int = QUALITY_MEDIUM,
        exclude_duplicates: bool = True,
        exclude_suspicious: bool = False
    ) -> pd.DataFrame:
        """
        Filter DataFrame by quality criteria.
        
        Args:
            df: Validated DataFrame
            min_score: Minimum quality score to include
            exclude_duplicates: Whether to exclude duplicate content
            exclude_suspicious: Whether to exclude suspicious authors
            
        Returns:
            Filtered DataFrame
        """
        filtered = df.copy()
        original_count = len(filtered)
        
        # Apply quality score filter
        filtered = filtered[filtered['quality_score'] >= min_score]
        
        # Exclude duplicates
        if exclude_duplicates and 'is_duplicate' in filtered.columns:
            filtered = filtered[~filtered['is_duplicate']]
        
        # Exclude suspicious authors
        if exclude_suspicious and 'is_suspicious_author' in filtered.columns:
            filtered = filtered[~filtered['is_suspicious_author']]
        
        removed_count = original_count - len(filtered)
        logger.info(f"Filtered {removed_count} posts. Remaining: {len(filtered)}")
        
        return filtered
    
    def get_validation_summary(self, df: pd.DataFrame) -> Dict:
        """
        Get summary statistics for validation results.
        
        Args:
            df: Validated DataFrame
            
        Returns:
            Dict with validation summary
        """
        if 'quality_level' not in df.columns:
            return {"error": "DataFrame not validated"}
        
        total = len(df)
        
        # Count by quality level
        high_count = (df['quality_level'] == 'high').sum()
        medium_count = (df['quality_level'] == 'medium').sum()
        low_count = (df['quality_level'] == 'low').sum()
        
        # Count issues
        all_issues = []
        for issues in df['quality_issues']:
            all_issues.extend(issues)
        issue_counts = Counter(all_issues)
        
        # Count duplicates and suspicious
        duplicate_count = df['is_duplicate'].sum() if 'is_duplicate' in df.columns else 0
        suspicious_count = df['is_suspicious_author'].sum() if 'is_suspicious_author' in df.columns else 0
        
        return {
            'total_posts': total,
            'high_quality': int(high_count),
            'medium_quality': int(medium_count),
            'low_quality': int(low_count),
            'high_percentage': round(high_count / total * 100, 1) if total > 0 else 0,
            'medium_percentage': round(medium_count / total * 100, 1) if total > 0 else 0,
            'low_percentage': round(low_count / total * 100, 1) if total > 0 else 0,
            'valid_count': int((df['is_valid']).sum()) if 'is_valid' in df.columns else 0,
            'invalid_count': int((~df['is_valid']).sum()) if 'is_valid' in df.columns else 0,
            'duplicate_count': int(duplicate_count),
            'suspicious_author_count': int(suspicious_count),
            'issue_breakdown': dict(issue_counts),
            'avg_quality_score': round(df['quality_score'].mean(), 1),
        }


def get_issue_description(issue: str) -> str:
    """Get human-readable description for issue code."""
    descriptions = {
        'too_short': 'Çok kısa metin',
        'emoji_only': 'Sadece emoji/sembol',
        'too_many_urls': 'Çok fazla URL',
        'hashtag_spam': 'Aşırı hashtag kullanımı',
        'spam_keywords': 'Spam kelimeler içeriyor',
        'bot_pattern': 'Bot davranışı tespit edildi',
        'duplicate': 'Tekrarlayan içerik',
        'suspicious_author': 'Şüpheli yazar aktivitesi',
    }
    return descriptions.get(issue, issue)


def get_issue_descriptions(issues: List[str]) -> str:
    """Get comma-separated descriptions for multiple issues."""
    if not issues:
        return "Sorun yok"
    return ", ".join([get_issue_description(i) for i in issues])

