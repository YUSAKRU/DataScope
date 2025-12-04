"""
Data processing modules for DataScope.

This package contains modules for cleaning and normalizing data:
- cleaning: Text cleaning and preprocessing
- normalizer: Data normalization and standardization
- validation: Data quality validation and filtering
"""

from .cleaning import (
    clean_html,
    clean_urls,
    clean_mentions,
    clean_hashtags,
    clean_special_characters,
    normalize_whitespace,
    clean_text,
    remove_stopwords,
    validate_dataframe,
    process_dataframe,
    get_word_frequencies,
    TURKISH_STOPWORDS,
    REQUIRED_COLUMNS,
)

from .normalizer import (
    normalize_dates,
    normalize_counts,
    normalize_authors,
    normalize_text_encoding,
    calculate_engagement_score,
    add_engagement_metrics,
    normalize_dataframe,
    filter_by_date_range,
    filter_by_language,
    remove_duplicates,
)

from .validation import (
    DataValidator,
    get_issue_description,
    get_issue_descriptions,
    QUALITY_HIGH,
    QUALITY_MEDIUM,
    QUALITY_LOW,
    SPAM_KEYWORDS,
)

__all__ = [
    # Cleaning
    "clean_html",
    "clean_urls",
    "clean_mentions",
    "clean_hashtags",
    "clean_special_characters",
    "normalize_whitespace",
    "clean_text",
    "remove_stopwords",
    "validate_dataframe",
    "process_dataframe",
    "get_word_frequencies",
    "TURKISH_STOPWORDS",
    "REQUIRED_COLUMNS",
    # Normalizer
    "normalize_dates",
    "normalize_counts",
    "normalize_authors",
    "normalize_text_encoding",
    "calculate_engagement_score",
    "add_engagement_metrics",
    "normalize_dataframe",
    "filter_by_date_range",
    "filter_by_language",
    "remove_duplicates",
    # Validation
    "DataValidator",
    "get_issue_description",
    "get_issue_descriptions",
    "QUALITY_HIGH",
    "QUALITY_MEDIUM",
    "QUALITY_LOW",
    "SPAM_KEYWORDS",
]


