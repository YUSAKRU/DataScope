"""
Topic modeling module for DataScope.

This module provides topic extraction and analysis using LDA
(Latent Dirichlet Allocation) algorithm.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

import pandas as pd
import numpy as np

from ..utils.logger import get_logger
from ..processor.cleaning import TURKISH_STOPWORDS

logger = get_logger(__name__)

# Additional stopwords for topic modeling
TOPIC_STOPWORDS = TURKISH_STOPWORDS | {
    'rt', 'http', 'https', 'www', 'com', 'org', 'net',
    'amp', 'gt', 'lt', 've', 'veya', 'ama', 'fakat',
    'twitter', 'mastodon', 'toot', 'post',
}


class TopicModeler:
    """
    Topic modeling using LDA algorithm.
    
    Extracts latent topics from a collection of texts.
    
    Example:
        >>> modeler = TopicModeler(num_topics=5)
        >>> topics = modeler.fit_transform(df['cleaned_text'])
        >>> print(topics)
    """
    
    def __init__(
        self,
        num_topics: int = 5,
        max_features: int = 1000,
        min_df: int = 2,
        max_df: float = 0.95,
    ):
        """
        Initialize topic modeler.
        
        Args:
            num_topics: Number of topics to extract
            max_features: Maximum vocabulary size
            min_df: Minimum document frequency for terms
            max_df: Maximum document frequency ratio
        """
        self.num_topics = num_topics
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        
        self._vectorizer = None
        self._lda_model = None
        self._feature_names = None
        self._is_fitted = False
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for topic modeling."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        
        # Remove hashtag symbols but keep words
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove special characters, keep Turkish chars
        text = re.sub(r'[^\w\sçğıöşüÇĞİÖŞÜ]', ' ', text)
        
        # Remove stopwords
        words = text.split()
        words = [w for w in words if w not in TOPIC_STOPWORDS and len(w) > 2]
        
        return ' '.join(words)
    
    def fit_transform(self, texts: List[str]) -> Dict[str, Any]:
        """
        Fit the model and extract topics.
        
        Args:
            texts: List of text documents
            
        Returns:
            Dict containing:
                - topics: List of topics with keywords
                - document_topics: Topic distribution per document
                - coherence_score: Topic coherence (if available)
        """
        try:
            from sklearn.feature_extraction.text import CountVectorizer
            from sklearn.decomposition import LatentDirichletAllocation
        except ImportError:
            logger.error("scikit-learn not installed")
            return self._fallback_topics(texts)
        
        # Preprocess texts
        processed_texts = [self._preprocess_text(t) for t in texts]
        
        # Filter empty texts
        valid_indices = [i for i, t in enumerate(processed_texts) if t.strip()]
        valid_texts = [processed_texts[i] for i in valid_indices]
        
        if len(valid_texts) < self.num_topics:
            logger.warning(f"Not enough documents ({len(valid_texts)}) for {self.num_topics} topics")
            return self._fallback_topics(texts)
        
        # Vectorize
        self._vectorizer = CountVectorizer(
            max_features=self.max_features,
            min_df=self.min_df,
            max_df=self.max_df,
            stop_words=list(TOPIC_STOPWORDS)
        )
        
        try:
            doc_term_matrix = self._vectorizer.fit_transform(valid_texts)
        except ValueError as e:
            logger.warning(f"Vectorization failed: {e}")
            return self._fallback_topics(texts)
        
        self._feature_names = self._vectorizer.get_feature_names_out()
        
        # Fit LDA
        self._lda_model = LatentDirichletAllocation(
            n_components=self.num_topics,
            random_state=42,
            max_iter=20,
            learning_method='online',
            n_jobs=-1
        )
        
        doc_topic_matrix = self._lda_model.fit_transform(doc_term_matrix)
        
        self._is_fitted = True
        
        # Extract topics
        topics = self._extract_topics(n_words=10)
        
        # Map back to original indices
        document_topics = [None] * len(texts)
        for idx, valid_idx in enumerate(valid_indices):
            document_topics[valid_idx] = {
                'dominant_topic': int(np.argmax(doc_topic_matrix[idx])),
                'topic_distribution': doc_topic_matrix[idx].tolist()
            }
        
        logger.info(f"Extracted {self.num_topics} topics from {len(valid_texts)} documents")
        
        return {
            'topics': topics,
            'document_topics': document_topics,
            'num_documents': len(valid_texts),
            'vocabulary_size': len(self._feature_names),
        }
    
    def _extract_topics(self, n_words: int = 10) -> List[Dict]:
        """Extract top words for each topic."""
        topics = []
        
        for topic_idx, topic in enumerate(self._lda_model.components_):
            top_indices = topic.argsort()[:-n_words-1:-1]
            top_words = [self._feature_names[i] for i in top_indices]
            top_weights = [float(topic[i]) for i in top_indices]
            
            topics.append({
                'id': topic_idx,
                'name': f"Konu {topic_idx + 1}",
                'keywords': top_words,
                'weights': top_weights,
                'top_keyword': top_words[0] if top_words else "",
            })
        
        return topics
    
    def _fallback_topics(self, texts: List[str]) -> Dict[str, Any]:
        """
        Fallback topic extraction using simple word frequency.
        Used when LDA fails or not enough data.
        """
        logger.info("Using fallback topic extraction (word frequency)")
        
        # Collect all words
        all_words = []
        for text in texts:
            processed = self._preprocess_text(text)
            all_words.extend(processed.split())
        
        # Get most common words
        word_counts = Counter(all_words)
        top_words = word_counts.most_common(50)
        
        # Create pseudo-topics from top words
        words_per_topic = max(5, len(top_words) // self.num_topics)
        topics = []
        
        for i in range(min(self.num_topics, len(top_words) // words_per_topic)):
            start = i * words_per_topic
            end = start + words_per_topic
            topic_words = [w for w, _ in top_words[start:end]]
            topic_weights = [float(c) for _, c in top_words[start:end]]
            
            topics.append({
                'id': i,
                'name': f"Konu {i + 1}",
                'keywords': topic_words,
                'weights': topic_weights,
                'top_keyword': topic_words[0] if topic_words else "",
            })
        
        return {
            'topics': topics,
            'document_topics': [None] * len(texts),
            'num_documents': len(texts),
            'vocabulary_size': len(word_counts),
            'is_fallback': True,
        }
    
    def get_topic_summary(self, topics_result: Dict) -> str:
        """Generate a text summary of topics."""
        lines = ["📚 Konu Analizi Özeti", "=" * 40]
        
        for topic in topics_result.get('topics', []):
            keywords = ", ".join(topic['keywords'][:5])
            lines.append(f"\n🏷️ {topic['name']}: {keywords}")
        
        return "\n".join(lines)


def analyze_topics(df: pd.DataFrame, text_column: str = 'cleaned_text', num_topics: int = 5) -> Dict:
    """
    Convenience function to analyze topics in a DataFrame.
    
    Args:
        df: DataFrame with text data
        text_column: Column containing text (auto-detected if not found)
        num_topics: Number of topics to extract
        
    Returns:
        Topic analysis results
    """
    if text_column not in df.columns:
        # Try alternative columns
        for alt in ['cleaned_text', 'content', 'text']:
            if alt in df.columns:
                text_column = alt
                break
        else:
            return {"error": f"Text column not found"}
    
    texts = df[text_column].fillna('').tolist()
    
    modeler = TopicModeler(num_topics=num_topics)
    results = modeler.fit_transform(texts)
    
    # Add document topics to result
    if results.get('document_topics'):
        topic_assignments = []
        for dt in results['document_topics']:
            if dt:
                topic_assignments.append(dt['dominant_topic'])
            else:
                topic_assignments.append(-1)
        
        # Count documents per topic
        topic_counts = Counter(topic_assignments)
        for topic in results.get('topics', []):
            topic['document_count'] = topic_counts.get(topic['id'], 0)
    
    results['summary'] = modeler.get_topic_summary(results)
    
    return results


