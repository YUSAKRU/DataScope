"""
Analysis modules for DataScope.

This package contains comprehensive analysis modules:
- sentiment: Sentiment analysis using Google Cloud NLP
- statistics: Statistical analysis and reporting
- topic_modeling: LDA topic extraction
- keywords: TF-IDF and RAKE keyword extraction
- network: Social network analysis (hashtags, mentions)
- temporal: Time-based trend and pattern analysis
- author_profiling: User influence and activity analysis
- text_classification: Rule-based text categorization
"""

from .sentiment import (
    SentimentAnalyzer,
    get_sentiment_summary,
    POSITIVE_THRESHOLD,
    NEGATIVE_THRESHOLD,
    MAX_TEXT_LENGTH,
    MIN_TEXT_LENGTH,
)

from .statistics import (
    calculate_basic_stats,
    calculate_engagement_stats,
    calculate_temporal_stats,
    calculate_author_stats,
    calculate_sentiment_stats,
    calculate_sentiment_by_time,
    calculate_word_stats,
    generate_full_report,
)

from .topic_modeling import (
    TopicModeler,
    analyze_topics,
)

from .keywords import (
    KeywordExtractor,
    extract_keywords,
    get_keyword_summary,
)

from .network import (
    NetworkAnalyzer,
    analyze_network,
    get_network_summary,
)

from .temporal import (
    TemporalAnalyzer,
    analyze_temporal,
    get_temporal_summary,
)

from .author_profiling import (
    AuthorProfiler,
    profile_authors,
    get_author_summary,
)

from .text_classification import (
    TextClassifier,
    classify_texts,
    get_classification_summary,
    CATEGORY_DESCRIPTIONS,
)

__all__ = [
    # Sentiment
    "SentimentAnalyzer",
    "get_sentiment_summary",
    "POSITIVE_THRESHOLD",
    "NEGATIVE_THRESHOLD",
    "MAX_TEXT_LENGTH",
    "MIN_TEXT_LENGTH",
    # Statistics
    "calculate_basic_stats",
    "calculate_engagement_stats",
    "calculate_temporal_stats",
    "calculate_author_stats",
    "calculate_sentiment_stats",
    "calculate_sentiment_by_time",
    "calculate_word_stats",
    "generate_full_report",
    # Topic Modeling
    "TopicModeler",
    "analyze_topics",
    # Keywords
    "KeywordExtractor",
    "extract_keywords",
    "get_keyword_summary",
    # Network
    "NetworkAnalyzer",
    "analyze_network",
    "get_network_summary",
    # Temporal
    "TemporalAnalyzer",
    "analyze_temporal",
    "get_temporal_summary",
    # Author Profiling
    "AuthorProfiler",
    "profile_authors",
    "get_author_summary",
    # Text Classification
    "TextClassifier",
    "classify_texts",
    "get_classification_summary",
    "CATEGORY_DESCRIPTIONS",
]


