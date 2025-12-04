"""
Keyword extraction module for DataScope.

This module provides keyword and keyphrase extraction using
TF-IDF and RAKE algorithms with Turkish language support.
"""

import re
from typing import Dict, List, Tuple, Optional
from collections import Counter

import pandas as pd
import numpy as np

from ..utils.logger import get_logger
from ..processor.cleaning import TURKISH_STOPWORDS

logger = get_logger(__name__)


class KeywordExtractor:
    """
    Extract keywords and keyphrases from text.
    
    Uses TF-IDF for single keywords and custom RAKE-like algorithm
    for multi-word keyphrases with Turkish support.
    
    Example:
        >>> extractor = KeywordExtractor()
        >>> keywords = extractor.extract(texts)
        >>> print(keywords['tfidf_keywords'])
    """
    
    def __init__(
        self,
        max_keywords: int = 20,
        ngram_range: Tuple[int, int] = (1, 3),
        min_df: int = 2,
    ):
        """
        Initialize keyword extractor.
        
        Args:
            max_keywords: Maximum keywords to extract
            ngram_range: Range for n-gram extraction (min, max)
            min_df: Minimum document frequency
        """
        self.max_keywords = max_keywords
        self.ngram_range = ngram_range
        self.min_df = min_df
        
        self._vectorizer = None
        self._tfidf_matrix = None
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for keyword extraction."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        
        # Keep hashtag words
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\sçğıöşüÇĞİÖŞÜ]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def extract_tfidf(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Extract keywords using TF-IDF.
        
        Args:
            texts: List of text documents
            
        Returns:
            List of (keyword, score) tuples sorted by score
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError:
            logger.error("scikit-learn not installed")
            return self._fallback_keywords(texts)
        
        # Preprocess
        processed_texts = [self._preprocess_text(t) for t in texts]
        
        # Filter empty
        valid_texts = [t for t in processed_texts if t.strip()]
        
        if len(valid_texts) < self.min_df:
            return self._fallback_keywords(texts)
        
        # Create TF-IDF vectorizer
        self._vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            min_df=min(self.min_df, len(valid_texts)),
            max_df=0.95,
            stop_words=list(TURKISH_STOPWORDS),
            token_pattern=r'(?u)\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{2,}\b'
        )
        
        try:
            self._tfidf_matrix = self._vectorizer.fit_transform(valid_texts)
        except ValueError:
            return self._fallback_keywords(texts)
        
        # Get feature names and scores
        feature_names = self._vectorizer.get_feature_names_out()
        
        # Sum TF-IDF scores across documents
        tfidf_scores = np.array(self._tfidf_matrix.sum(axis=0)).flatten()
        
        # Create keyword-score pairs
        keyword_scores = list(zip(feature_names, tfidf_scores))
        
        # Sort by score and get top keywords
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        return keyword_scores[:self.max_keywords]
    
    def extract_rake(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Extract keyphrases using RAKE-like algorithm.
        
        RAKE (Rapid Automatic Keyword Extraction) identifies
        multi-word keyphrases based on word co-occurrence.
        
        Args:
            texts: List of text documents
            
        Returns:
            List of (keyphrase, score) tuples
        """
        # Collect candidate phrases
        phrase_freq = Counter()
        word_scores = {}
        
        for text in texts:
            processed = self._preprocess_text(text)
            
            # Split by stopwords to get candidate phrases
            words = processed.split()
            current_phrase = []
            
            for word in words:
                if word in TURKISH_STOPWORDS or len(word) < 3:
                    if current_phrase:
                        phrase = ' '.join(current_phrase)
                        if len(phrase) > 3:
                            phrase_freq[phrase] += 1
                        current_phrase = []
                else:
                    current_phrase.append(word)
            
            # Don't forget last phrase
            if current_phrase:
                phrase = ' '.join(current_phrase)
                if len(phrase) > 3:
                    phrase_freq[phrase] += 1
        
        # Calculate RAKE score for each phrase
        # Score = sum of word degrees / sum of word frequencies
        word_freq = Counter()
        word_degree = Counter()
        
        for phrase, freq in phrase_freq.items():
            words = phrase.split()
            for word in words:
                word_freq[word] += freq
                word_degree[word] += freq * (len(words) - 1)
        
        # Calculate word scores
        for word in word_freq:
            word_scores[word] = (word_degree[word] + word_freq[word]) / word_freq[word]
        
        # Calculate phrase scores
        phrase_scores = []
        for phrase, freq in phrase_freq.items():
            words = phrase.split()
            score = sum(word_scores.get(w, 0) for w in words)
            phrase_scores.append((phrase, score * freq))
        
        # Sort and return top phrases
        phrase_scores.sort(key=lambda x: x[1], reverse=True)
        
        return phrase_scores[:self.max_keywords]
    
    def extract_ngrams(self, texts: List[str], n: int = 2) -> List[Tuple[str, int]]:
        """
        Extract n-grams from texts.
        
        Args:
            texts: List of text documents
            n: N-gram size (2 for bigram, 3 for trigram)
            
        Returns:
            List of (ngram, count) tuples
        """
        ngram_counts = Counter()
        
        for text in texts:
            processed = self._preprocess_text(text)
            words = [w for w in processed.split() 
                    if w not in TURKISH_STOPWORDS and len(w) > 2]
            
            # Generate n-grams
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                ngram_counts[ngram] += 1
        
        return ngram_counts.most_common(self.max_keywords)
    
    def _fallback_keywords(self, texts: List[str]) -> List[Tuple[str, float]]:
        """Fallback to simple word frequency."""
        word_counts = Counter()
        
        for text in texts:
            processed = self._preprocess_text(text)
            words = [w for w in processed.split() 
                    if w not in TURKISH_STOPWORDS and len(w) > 2]
            word_counts.update(words)
        
        return [(w, float(c)) for w, c in word_counts.most_common(self.max_keywords)]
    
    def extract_all(self, texts: List[str]) -> Dict:
        """
        Extract keywords using all methods.
        
        Args:
            texts: List of text documents
            
        Returns:
            Dict with keywords from each method
        """
        logger.info(f"Extracting keywords from {len(texts)} documents")
        
        results = {
            'tfidf_keywords': self.extract_tfidf(texts),
            'rake_keyphrases': self.extract_rake(texts),
            'bigrams': self.extract_ngrams(texts, n=2),
            'trigrams': self.extract_ngrams(texts, n=3),
            'document_count': len(texts),
        }
        
        # Create combined top keywords
        all_keywords = {}
        for kw, score in results['tfidf_keywords']:
            all_keywords[kw] = all_keywords.get(kw, 0) + score
        for kw, score in results['rake_keyphrases']:
            all_keywords[kw] = all_keywords.get(kw, 0) + score * 0.5
        
        top_combined = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)
        results['top_keywords'] = top_combined[:self.max_keywords]
        
        logger.info(f"Extracted {len(results['top_keywords'])} top keywords")
        
        return results


def extract_keywords(df: pd.DataFrame, text_column: str = 'cleaned_text') -> Dict:
    """
    Convenience function to extract keywords from DataFrame.
    
    Args:
        df: DataFrame with text data
        text_column: Column containing text
        
    Returns:
        Keyword extraction results
    """
    if text_column not in df.columns:
        return {"error": f"Column '{text_column}' not found"}
    
    texts = df[text_column].fillna('').tolist()
    
    extractor = KeywordExtractor()
    results = extractor.extract_all(texts)
    
    # Add hashtag analysis - check multiple possible columns
    hashtag_col = None
    for col in ['cleaned_text', 'content', 'text']:
        if col in df.columns:
            hashtag_col = col
            break
    
    if hashtag_col:
        hashtag_counts = Counter()
        for content in df[hashtag_col].fillna(''):
            hashtags = re.findall(r'#(\w+)', str(content).lower())
            hashtag_counts.update(hashtags)
        results['hashtags'] = hashtag_counts.most_common(20)
    
    return results


def get_keyword_summary(results: Dict) -> str:
    """Generate text summary of keyword extraction."""
    lines = ["🔑 Anahtar Kelime Analizi", "=" * 40]
    
    # Top keywords
    lines.append("\n📊 En Önemli Anahtar Kelimeler:")
    for kw, score in results.get('top_keywords', [])[:10]:
        lines.append(f"  • {kw}: {score:.2f}")
    
    # Bigrams
    lines.append("\n📝 İkili Kelime Grupları (Bigrams):")
    for bg, count in results.get('bigrams', [])[:5]:
        lines.append(f"  • {bg}: {count}")
    
    # Hashtags
    if 'hashtags' in results:
        lines.append("\n#️⃣ Hashtag'ler:")
        for tag, count in results['hashtags'][:5]:
            lines.append(f"  • #{tag}: {count}")
    
    return "\n".join(lines)


