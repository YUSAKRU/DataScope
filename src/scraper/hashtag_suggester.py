"""
Hashtag suggestion module for DataScope.

This module provides intelligent hashtag suggestions based on:
- Live search results from Mastodon
- Trending hashtags analysis
- Semantic similarity scoring

Features:
- Multi-language support (Turkish, English, All)
- Fuzzy matching for relevance scoring
- Caching for performance optimization
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from mastodon import Mastodon, MastodonNetworkError, MastodonAPIError
from bs4 import BeautifulSoup

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Turkish character normalization map
TURKISH_CHAR_MAP = {
    'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
    'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
    'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
}

# Common Turkish words for language detection
TURKISH_INDICATORS = {
    've', 'bir', 'bu', 'için', 'ile', 'da', 'de', 'den', 'dan',
    'çok', 'gibi', 'daha', 'var', 'olan', 'olarak', 'sonra',
    'kadar', 'ancak', 'ama', 'fakat', 'veya', 'ya', 'hem',
    'iklim', 'çevre', 'doğa', 'sürdürülebilir', 'enerji',
    'haber', 'gündem', 'türkiye', 'istanbul', 'ankara'
}

# Common research-related hashtag mappings
RESEARCH_TOPIC_HASHTAGS = {
    'iklim': ['iklim', 'climate', 'climatechange', 'iklimkrizi', 'iklimdeğişikliği', 
              'globalwarming', 'çevre', 'environment', 'sustainability'],
    'climate': ['climate', 'iklim', 'climatechange', 'globalwarming', 'climateaction',
                'climatecrisis', 'environment', 'sustainability', 'greennewdeal'],
    'sağlık': ['sağlık', 'health', 'healthcare', 'medical', 'tıp', 'hastane'],
    'health': ['health', 'sağlık', 'healthcare', 'wellness', 'medical', 'medicine'],
    'teknoloji': ['teknoloji', 'technology', 'tech', 'dijital', 'yapayZeka', 'ai'],
    'technology': ['technology', 'teknoloji', 'tech', 'digital', 'ai', 'innovation'],
    'eğitim': ['eğitim', 'education', 'öğrenci', 'okul', 'üniversite', 'learning'],
    'education': ['education', 'eğitim', 'learning', 'school', 'university', 'students'],
    'ekonomi': ['ekonomi', 'economy', 'finans', 'piyasa', 'borsa', 'dolar'],
    'economy': ['economy', 'ekonomi', 'finance', 'market', 'business', 'stocks'],
    'siyaset': ['siyaset', 'politics', 'seçim', 'hükümet', 'demokrasi'],
    'politics': ['politics', 'siyaset', 'election', 'democracy', 'government'],
}


class HashtagSuggester:
    """
    Intelligent hashtag suggestion system.
    
    Combines live Mastodon search, trending analysis, and semantic
    similarity to suggest the most relevant hashtags for research topics.
    
    Example:
        >>> suggester = HashtagSuggester("https://mastodon.social")
        >>> suggestions = suggester.suggest_hashtags("iklim değişikliği", limit=10)
        >>> for s in suggestions:
        ...     print(f"#{s['hashtag']}: {s['score']:.2f}")
    """
    
    def __init__(self, instance_url: str = "https://mastodon.social") -> None:
        """
        Initialize the hashtag suggester.
        
        Args:
            instance_url: Mastodon instance URL
        """
        self.instance_url = instance_url
        self._client = None
        self._cache = {}
        self._cache_ttl = timedelta(hours=1)
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Mastodon client."""
        try:
            self._client = Mastodon(api_base_url=self.instance_url)
            logger.info(f"HashtagSuggester initialized for: {self.instance_url}")
        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            self._client = None
    
    def normalize_text(self, text: str, to_ascii: bool = False) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: Input text
            to_ascii: Convert Turkish chars to ASCII equivalents
            
        Returns:
            Normalized text
        """
        text = text.lower().strip()
        
        if to_ascii:
            for tr_char, en_char in TURKISH_CHAR_MAP.items():
                text = text.replace(tr_char.lower(), en_char.lower())
        
        return text
    
    def detect_language(self, text: str) -> str:
        """
        Detect if text is primarily Turkish or English.
        
        Args:
            text: Input text
            
        Returns:
            'tr' for Turkish, 'en' for English, 'unknown' otherwise
        """
        text_lower = text.lower()
        words = set(re.findall(r'\w+', text_lower))
        
        # Check for Turkish specific characters
        has_turkish_chars = bool(re.search(r'[ıİğĞüÜşŞöÖçÇ]', text))
        
        # Check for Turkish words
        turkish_word_count = len(words.intersection(TURKISH_INDICATORS))
        
        if has_turkish_chars or turkish_word_count >= 1:
            return 'tr'
        
        return 'en'
    
    def is_turkish_hashtag(self, hashtag: str) -> bool:
        """Check if hashtag appears to be Turkish."""
        hashtag_lower = hashtag.lower()
        
        # Check for Turkish characters
        if re.search(r'[ıİğĞüÜşŞöÖçÇ]', hashtag):
            return True
        
        # Check common Turkish hashtag patterns
        turkish_patterns = [
            'turkiye', 'türkiye', 'istanbul', 'ankara', 'izmir',
            'gundem', 'gündem', 'haber', 'son', 'bugun', 'bugün'
        ]
        
        for pattern in turkish_patterns:
            if pattern in hashtag_lower:
                return True
        
        return False
    
    def get_trending_hashtags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get trending hashtags from Mastodon instance.
        
        Args:
            limit: Maximum number of trending hashtags
            
        Returns:
            List of trending hashtag data
        """
        cache_key = f"trending_{self.instance_url}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < self._cache_ttl:
                logger.debug("Returning cached trending hashtags")
                return cached_data
        
        if not self._client:
            logger.warning("Client not initialized, returning empty list")
            return []
        
        try:
            trending = self._client.trending_tags()
            
            results = []
            for tag in trending[:limit]:
                results.append({
                    'hashtag': tag['name'],
                    'usage_count': sum(int(h.get('uses', 0)) for h in tag.get('history', [])),
                    'accounts': sum(int(h.get('accounts', 0)) for h in tag.get('history', [])),
                    'is_trending': True,
                    'url': tag.get('url', ''),
                })
            
            # Cache results
            self._cache[cache_key] = (results, datetime.now())
            logger.info(f"Fetched {len(results)} trending hashtags")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching trending hashtags: {e}")
            return []
    
    def search_related_hashtags(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Search for hashtags related to a query by analyzing posts.
        
        Args:
            query: Search query (topic/keyword)
            limit: Maximum posts to analyze
            
        Returns:
            List of related hashtags with frequency
        """
        cache_key = f"search_{query}_{limit}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < self._cache_ttl:
                logger.debug(f"Returning cached search results for '{query}'")
                return cached_data
        
        if not self._client:
            return []
        
        hashtag_counter = Counter()
        
        try:
            # Search by query as hashtag
            normalized_query = re.sub(r'\s+', '', query.lower())
            
            # Try to fetch posts with this hashtag
            try:
                posts = self._client.timeline_hashtag(normalized_query, limit=limit)
            except:
                posts = []
            
            # Also do a general search
            try:
                search_results = self._client.search_v2(query, result_type='statuses')
                posts.extend(search_results.get('statuses', [])[:limit])
            except:
                pass
            
            # Extract hashtags from posts
            for post in posts:
                content = post.get('content', '')
                
                # Parse HTML content
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text()
                
                # Find hashtags
                hashtags = re.findall(r'#(\w+)', text)
                
                # Also check tags field
                for tag in post.get('tags', []):
                    hashtags.append(tag.get('name', ''))
                
                # Count hashtags (excluding the query itself)
                for ht in hashtags:
                    ht_lower = ht.lower()
                    if ht_lower and ht_lower != normalized_query:
                        hashtag_counter[ht_lower] += 1
            
            # Convert to results
            results = []
            for hashtag, count in hashtag_counter.most_common(50):
                results.append({
                    'hashtag': hashtag,
                    'frequency': count,
                    'source': 'search',
                })
            
            # Cache results
            self._cache[cache_key] = (results, datetime.now())
            logger.info(f"Found {len(results)} related hashtags for '{query}'")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching hashtags: {e}")
            return []
    
    def calculate_relevance_score(self, query: str, hashtag: str) -> float:
        """
        Calculate relevance score between query and hashtag.
        
        Uses multiple methods:
        - Exact/partial match
        - Sequence similarity (fuzzy matching)
        - Normalized form comparison
        
        Args:
            query: Original search query
            hashtag: Hashtag to score
            
        Returns:
            Relevance score (0-100)
        """
        query_normalized = self.normalize_text(query, to_ascii=True)
        hashtag_normalized = self.normalize_text(hashtag, to_ascii=True)
        
        # Remove spaces from query for comparison
        query_compact = re.sub(r'\s+', '', query_normalized)
        
        # Exact match
        if query_compact == hashtag_normalized:
            return 100.0
        
        # Contains check
        if query_compact in hashtag_normalized or hashtag_normalized in query_compact:
            return 85.0
        
        # Check individual words
        query_words = set(query_normalized.split())
        hashtag_words = set(re.findall(r'[a-z]+', hashtag_normalized))
        
        word_overlap = len(query_words.intersection(hashtag_words))
        if word_overlap > 0:
            overlap_score = (word_overlap / max(len(query_words), 1)) * 70
            return min(80, overlap_score + 20)
        
        # Sequence similarity (Levenshtein-like)
        similarity = SequenceMatcher(None, query_compact, hashtag_normalized).ratio()
        
        return similarity * 60
    
    def get_predefined_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """
        Get predefined hashtag suggestions for common research topics.
        
        Args:
            query: Search query
            
        Returns:
            List of suggested hashtags
        """
        query_normalized = self.normalize_text(query, to_ascii=True)
        suggestions = []
        
        for topic, hashtags in RESEARCH_TOPIC_HASHTAGS.items():
            topic_normalized = self.normalize_text(topic, to_ascii=True)
            
            if topic_normalized in query_normalized or query_normalized in topic_normalized:
                for ht in hashtags:
                    suggestions.append({
                        'hashtag': ht,
                        'source': 'predefined',
                        'topic_match': topic,
                    })
        
        return suggestions
    
    def suggest_hashtags(
        self, 
        query: str, 
        limit: int = 10,
        language_filter: str = 'all',
        include_trending: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get intelligent hashtag suggestions for a research topic.
        
        Args:
            query: Research topic/keyword
            limit: Maximum suggestions to return
            language_filter: 'all', 'tr' (Turkish only), 'en' (English only)
            include_trending: Include trending hashtags in results
            
        Returns:
            List of suggested hashtags with scores
        """
        logger.info(f"Generating hashtag suggestions for: '{query}' (lang={language_filter})")
        
        all_suggestions = {}
        
        # 1. Get predefined suggestions
        predefined = self.get_predefined_suggestions(query)
        for item in predefined:
            ht = item['hashtag'].lower()
            if ht not in all_suggestions:
                all_suggestions[ht] = {
                    'hashtag': item['hashtag'],
                    'frequency_score': 0,
                    'trend_score': 50,  # Predefined get moderate trend score
                    'relevance_score': 80,  # High relevance for predefined matches
                    'sources': ['predefined'],
                }
            else:
                all_suggestions[ht]['sources'].append('predefined')
        
        # 2. Search for related hashtags
        search_results = self.search_related_hashtags(query, limit=50)
        max_freq = max((r['frequency'] for r in search_results), default=1)
        
        for item in search_results:
            ht = item['hashtag'].lower()
            freq_score = (item['frequency'] / max_freq) * 100
            rel_score = self.calculate_relevance_score(query, ht)
            
            if ht not in all_suggestions:
                all_suggestions[ht] = {
                    'hashtag': item['hashtag'],
                    'frequency_score': freq_score,
                    'trend_score': 0,
                    'relevance_score': rel_score,
                    'sources': ['search'],
                }
            else:
                all_suggestions[ht]['frequency_score'] = max(
                    all_suggestions[ht]['frequency_score'], freq_score
                )
                all_suggestions[ht]['relevance_score'] = max(
                    all_suggestions[ht]['relevance_score'], rel_score
                )
                if 'search' not in all_suggestions[ht]['sources']:
                    all_suggestions[ht]['sources'].append('search')
        
        # 3. Add trending hashtags
        if include_trending:
            trending = self.get_trending_hashtags(limit=20)
            max_usage = max((t['usage_count'] for t in trending), default=1)
            
            for item in trending:
                ht = item['hashtag'].lower()
                trend_score = (item['usage_count'] / max_usage) * 100
                rel_score = self.calculate_relevance_score(query, ht)
                
                if ht not in all_suggestions:
                    all_suggestions[ht] = {
                        'hashtag': item['hashtag'],
                        'frequency_score': 0,
                        'trend_score': trend_score,
                        'relevance_score': rel_score,
                        'sources': ['trending'],
                        'is_trending': True,
                    }
                else:
                    all_suggestions[ht]['trend_score'] = trend_score
                    all_suggestions[ht]['is_trending'] = True
                    if 'trending' not in all_suggestions[ht]['sources']:
                        all_suggestions[ht]['sources'].append('trending')
        
        # 4. Calculate final scores
        results = []
        for ht, data in all_suggestions.items():
            # Weighted score formula
            final_score = (
                data['frequency_score'] * 0.35 +
                data['trend_score'] * 0.25 +
                data['relevance_score'] * 0.40
            )
            
            # Bonus for multiple sources
            if len(data['sources']) > 1:
                final_score += 5 * (len(data['sources']) - 1)
            
            # Apply language filter
            is_turkish = self.is_turkish_hashtag(ht)
            
            if language_filter == 'tr' and not is_turkish:
                # Skip non-Turkish hashtags
                # But keep if it has high relevance
                if data['relevance_score'] < 70:
                    continue
            elif language_filter == 'en' and is_turkish:
                # Skip Turkish hashtags for English filter
                if data['relevance_score'] < 70:
                    continue
            
            results.append({
                'hashtag': data['hashtag'],
                'score': round(min(100, final_score), 1),
                'frequency_score': round(data['frequency_score'], 1),
                'trend_score': round(data['trend_score'], 1),
                'relevance_score': round(data['relevance_score'], 1),
                'sources': data['sources'],
                'is_trending': data.get('is_trending', False),
                'is_turkish': is_turkish,
            })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Generated {len(results[:limit])} suggestions")
        
        return results[:limit]
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache = {}
        logger.info("Cache cleared")


def suggest_hashtags(
    query: str,
    instance_url: str = "https://mastodon.social",
    limit: int = 10,
    language_filter: str = 'all'
) -> List[Dict[str, Any]]:
    """
    Convenience function to get hashtag suggestions.
    
    Args:
        query: Research topic/keyword
        instance_url: Mastodon instance URL
        limit: Maximum suggestions
        language_filter: 'all', 'tr', or 'en'
        
    Returns:
        List of hashtag suggestions
    """
    suggester = HashtagSuggester(instance_url)
    return suggester.suggest_hashtags(query, limit=limit, language_filter=language_filter)

