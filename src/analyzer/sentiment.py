"""
Sentiment analysis module for DataScope.

This module provides sentiment analysis using Google Cloud Natural Language API.
It supports both single text and batch analysis.
"""

import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd

from ..utils.exceptions import (
    CredentialsError,
    QuotaExceededError,
    TextTooLongError,
    EmptyTextError,
    AnalysisError,
)
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)

# Default credentials paths to check
CREDENTIALS_PATHS = [
    Path(__file__).parent.parent.parent / "credentials" / "service-account-key.json",
    Path.home() / ".config" / "gcloud" / "application_default_credentials.json",
]

# Sentiment thresholds
POSITIVE_THRESHOLD = 0.25
NEGATIVE_THRESHOLD = -0.25

# Text limits
MIN_TEXT_LENGTH = 1
MAX_TEXT_LENGTH = 5000

# Rate limiting
REQUESTS_PER_SECOND = 5
REQUEST_DELAY = 1.0 / REQUESTS_PER_SECOND


class SentimentAnalyzer:
    """
    Sentiment analyzer using Google Cloud Natural Language API.
    
    This class provides methods to analyze sentiment of texts using
    Google Cloud's Natural Language API.
    
    Requirements:
        - Google Cloud account
        - Natural Language API enabled
        - Service account key JSON file
        - GOOGLE_APPLICATION_CREDENTIALS environment variable set
        
    Example:
        >>> analyzer = SentimentAnalyzer()
        >>> result = analyzer.analyze("Bu çok güzel bir haber!")
        >>> print(result)
        {'score': 0.8, 'magnitude': 0.9, 'label': 'positive'}
    """
    
    def __init__(self) -> None:
        """
        Initialize the sentiment analyzer.
        
        Raises:
            CredentialsError: If API credentials are missing or invalid
        """
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """
        Initialize the Google Cloud Language client.
        
        Automatically searches for credentials in common locations.
        Falls back to mock mode if credentials are not available.
        """
        self._using_real_api = False
        credentials_path = None
        
        # First check environment variable
        env_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if env_path and os.path.exists(env_path):
            credentials_path = env_path
            logger.info(f"Using credentials from env: {credentials_path}")
        else:
            # Env var not set or file doesn't exist - search in default locations
            for path in CREDENTIALS_PATHS:
                if path.exists():
                    credentials_path = str(path.resolve())
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                    logger.info(f"Found credentials at: {credentials_path}")
                    break
        
        if not credentials_path:
            logger.warning("⚠️ Google Cloud credentials not found - running in MOCK mode")
            logger.warning("   For real AI analysis, add service-account-key.json to credentials/")
            self._client = None
            return
        
        try:
            from google.cloud import language_v1
            
            self._client = language_v1.LanguageServiceClient()
            self._using_real_api = True
            logger.info("✅ Google Cloud Language API initialized successfully!")
            logger.info(f"   Credentials: {credentials_path}")
            
        except ImportError:
            logger.warning("⚠️ google-cloud-language not installed - running in MOCK mode")
            logger.warning("   Install with: pip install google-cloud-language")
            self._client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Cloud API: {e}")
            logger.warning("   Falling back to MOCK mode")
            self._client = None
    
    @property
    def is_using_real_api(self) -> bool:
        """Check if using real Google Cloud API or mock mode."""
        return self._using_real_api
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Text to analyze (min 1, max 5000 characters)
            
        Returns:
            Dict:
                - score: float - Sentiment score (-1.0 to 1.0)
                - magnitude: float - Sentiment magnitude (0.0 to inf)
                - label: str - Sentiment label ("positive", "negative", "neutral")
                
        Raises:
            EmptyTextError: If text is empty
            TextTooLongError: If text exceeds maximum length
            QuotaExceededError: If API quota is exceeded
            AnalysisError: For other analysis errors
        """
        # Validate text
        if not text or not text.strip():
            raise EmptyTextError()
        
        text = text.strip()
        
        if len(text) > MAX_TEXT_LENGTH:
            raise TextTooLongError(len(text), MAX_TEXT_LENGTH)
        
        # Use mock mode if no client
        if self._client is None:
            return self._mock_analyze(text)
        
        try:
            from google.cloud import language_v1
            
            # Create document
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT,
                language="tr"  # Turkish
            )
            
            # Analyze sentiment
            response = self._client.analyze_sentiment(
                request={"document": document}
            )
            
            sentiment = response.document_sentiment
            score = sentiment.score
            magnitude = sentiment.magnitude
            
            # Determine label
            label = self._score_to_label(score)
            
            return {
                "score": round(score, 4),
                "magnitude": round(magnitude, 4),
                "label": label,
            }
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "quota" in error_str or "limit" in error_str:
                raise QuotaExceededError()
            elif "credentials" in error_str or "permission" in error_str:
                raise CredentialsError(str(e))
            else:
                raise AnalysisError(f"Sentiment analysis failed: {e}")
    
    def analyze_batch(
        self, 
        texts: List[str], 
        show_progress: bool = True
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Analyze sentiment of multiple texts.
        
        Args:
            texts: List of texts to analyze
            show_progress: Whether to show progress (default: True)
            
        Returns:
            List[Optional[Dict]]: Analysis results for each text.
                                  Failed analyses return None.
                                  
        Note:
            - Rate limiting is automatically applied
            - Failed analyses don't stop the batch
        """
        results = []
        total = len(texts)
        
        logger.info(f"Starting batch sentiment analysis for {total} texts...")
        
        for i, text in enumerate(texts):
            try:
                result = self.analyze(text)
                results.append(result)
            except (EmptyTextError, TextTooLongError) as e:
                logger.debug(f"Skipping text {i+1}: {e}")
                results.append(None)
            except (QuotaExceededError, CredentialsError) as e:
                logger.error(f"Critical error at text {i+1}: {e}")
                # Fill remaining with None
                results.extend([None] * (total - len(results)))
                break
            except Exception as e:
                logger.warning(f"Error analyzing text {i+1}: {e}")
                results.append(None)
            
            # Rate limiting
            if self._client is not None:
                time.sleep(REQUEST_DELAY)
            
            # Progress logging
            if show_progress and (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{total} texts analyzed")
        
        successful = sum(1 for r in results if r is not None)
        logger.info(f"Batch analysis complete: {successful}/{total} successful")
        
        return results
    
    def analyze_dataframe(
        self, 
        df: pd.DataFrame, 
        text_column: str = 'cleaned_text'
    ) -> pd.DataFrame:
        """
        Analyze sentiment for all texts in a DataFrame.
        
        Args:
            df: DataFrame with text column
            text_column: Name of the text column (default: 'cleaned_text')
            
        Returns:
            pd.DataFrame: DataFrame with added columns:
                - sentiment_score: float
                - sentiment_magnitude: float
                - sentiment_label: str
        """
        df = df.copy()
        
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in DataFrame")
        
        texts = df[text_column].fillna('').tolist()
        results = self.analyze_batch(texts)
        
        # Extract results into columns
        df['sentiment_score'] = [r['score'] if r else None for r in results]
        df['sentiment_magnitude'] = [r['magnitude'] if r else None for r in results]
        df['sentiment_label'] = [r['label'] if r else None for r in results]
        
        return df
    
    def _score_to_label(self, score: float) -> str:
        """
        Convert sentiment score to label.
        
        Args:
            score: Sentiment score (-1.0 to 1.0)
            
        Returns:
            str: "positive", "negative", or "neutral"
        """
        if score >= POSITIVE_THRESHOLD:
            return "positive"
        elif score <= NEGATIVE_THRESHOLD:
            return "negative"
        else:
            return "neutral"
    
    def _mock_analyze(self, text: str) -> Dict[str, Any]:
        """
        Mock sentiment analysis for testing without API.
        
        Uses simple heuristics based on Turkish sentiment keywords.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict: Mock analysis result
        """
        text_lower = text.lower()
        
        # Simple keyword-based sentiment
        positive_words = {
            'güzel', 'iyi', 'harika', 'mükemmel', 'süper', 'muhteşem', 'olumlu',
            'başarılı', 'mutlu', 'sevindirici', 'umut', 'destek', 'teşekkür',
            'bravo', 'aferin', 'tebrik', 'sevgi', 'keyif', 'enfes', 'şahane',
        }
        
        negative_words = {
            'kötü', 'berbat', 'korkunç', 'felaket', 'üzücü', 'olumsuz', 'tehlike',
            'sorun', 'problem', 'kriz', 'endişe', 'kaygı', 'korku', 'öfke',
            'nefret', 'rezalet', 'başarısız', 'vahim', 'acı', 'zararlı',
        }
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        
        if total == 0:
            score = 0.0
        else:
            score = (positive_count - negative_count) / (total + 1)
            score = max(-1.0, min(1.0, score))
        
        magnitude = min(total * 0.2, 1.0)
        label = self._score_to_label(score)
        
        return {
            "score": round(score, 4),
            "magnitude": round(magnitude, 4),
            "label": label,
        }


def get_sentiment_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary statistics for sentiment analysis results.
    
    Args:
        df: DataFrame with sentiment columns
        
    Returns:
        Dict: Summary statistics
    """
    if 'sentiment_label' not in df.columns:
        raise ValueError("DataFrame must have 'sentiment_label' column")
    
    # Count by label
    label_counts = df['sentiment_label'].value_counts().to_dict()
    
    total = len(df)
    valid = df['sentiment_label'].notna().sum()
    
    # Calculate percentages
    positive_count = label_counts.get('positive', 0)
    negative_count = label_counts.get('negative', 0)
    neutral_count = label_counts.get('neutral', 0)
    
    return {
        "total_posts": total,
        "analyzed_posts": valid,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "positive_percentage": round(positive_count / valid * 100, 2) if valid > 0 else 0,
        "negative_percentage": round(negative_count / valid * 100, 2) if valid > 0 else 0,
        "neutral_percentage": round(neutral_count / valid * 100, 2) if valid > 0 else 0,
        "average_score": round(df['sentiment_score'].mean(), 4) if 'sentiment_score' in df.columns else None,
        "score_std": round(df['sentiment_score'].std(), 4) if 'sentiment_score' in df.columns else None,
    }

