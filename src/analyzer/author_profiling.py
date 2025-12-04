"""
Author profiling module for DataScope.

This module provides author/user analysis including
influence scoring, activity patterns, and topic preferences.
"""

from typing import Dict, List, Optional, Any
from collections import Counter, defaultdict
import re

import pandas as pd
import numpy as np

from ..utils.logger import get_logger

logger = get_logger(__name__)


class AuthorProfiler:
    """
    Profile authors/users based on their social media activity.
    
    Analyzes:
    - Influence score (based on engagement)
    - Activity patterns (when they post)
    - Topic preferences
    - Content style
    
    Example:
        >>> profiler = AuthorProfiler()
        >>> profiles = profiler.profile_authors(df)
        >>> print(profiles['top_influencers'])
    """
    
    def __init__(self, min_posts: int = 2):
        """
        Initialize author profiler.
        
        Args:
            min_posts: Minimum posts for profiling
        """
        self.min_posts = min_posts
    
    def profile_authors(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Profile all authors in the dataset.
        
        Args:
            df: DataFrame with author and engagement data
            
        Returns:
            Author profiling results
        """
        if 'author' not in df.columns:
            return {'error': "Column 'author' not found"}
        
        # Group by author
        author_groups = df.groupby('author')
        
        profiles = []
        
        for author, group in author_groups:
            if len(group) < self.min_posts:
                continue
            
            profile = self._create_profile(author, group)
            profiles.append(profile)
        
        # Sort by influence score
        profiles.sort(key=lambda x: x['influence_score'], reverse=True)
        
        # Calculate overall statistics
        results = {
            'profiles': profiles[:50],  # Top 50 authors
            'total_authors': df['author'].nunique(),
            'profiled_authors': len(profiles),
            'top_influencers': profiles[:10],
            'summary_stats': self._calculate_summary_stats(profiles),
            'author_categories': self._categorize_authors(profiles),
        }
        
        logger.info(f"Profiled {len(profiles)} authors from {results['total_authors']} total")
        
        return results
    
    def _create_profile(self, author: str, group: pd.DataFrame) -> Dict:
        """Create profile for a single author."""
        # Basic stats
        post_count = len(group)
        
        # Engagement metrics
        total_reblogs = group['reblogs_count'].sum() if 'reblogs_count' in group.columns else 0
        total_favs = group['favourites_count'].sum() if 'favourites_count' in group.columns else 0
        total_replies = group['replies_count'].sum() if 'replies_count' in group.columns else 0
        
        avg_engagement = (total_reblogs + total_favs + total_replies) / post_count
        
        # Calculate influence score (0-100)
        influence_score = self._calculate_influence_score(
            post_count, total_reblogs, total_favs, total_replies
        )
        
        # Activity pattern
        activity_pattern = self._analyze_activity_pattern(group)
        
        # Content analysis
        content_style = self._analyze_content_style(group)
        
        # Topics (hashtags)
        topics = self._extract_topics(group)
        
        return {
            'author': author,
            'post_count': int(post_count),
            'influence_score': round(influence_score, 2),
            'engagement': {
                'total_reblogs': int(total_reblogs),
                'total_favourites': int(total_favs),
                'total_replies': int(total_replies),
                'avg_per_post': round(avg_engagement, 2),
            },
            'activity_pattern': activity_pattern,
            'content_style': content_style,
            'topics': topics,
        }
    
    def _calculate_influence_score(
        self, 
        posts: int, 
        reblogs: int, 
        favs: int, 
        replies: int
    ) -> float:
        """
        Calculate influence score (0-100).
        
        Formula considers:
        - Post frequency
        - Engagement received
        - Engagement per post ratio
        """
        # Weights
        w_posts = 0.2
        w_reblogs = 0.35
        w_favs = 0.25
        w_replies = 0.2
        
        # Normalize using log scale
        log_posts = np.log1p(posts)
        log_reblogs = np.log1p(reblogs)
        log_favs = np.log1p(favs)
        log_replies = np.log1p(replies)
        
        # Calculate raw score
        raw_score = (
            w_posts * log_posts +
            w_reblogs * log_reblogs +
            w_favs * log_favs +
            w_replies * log_replies
        )
        
        # Scale to 0-100 (assuming max reasonable values)
        max_expected_score = 15  # Approximate max for very active users
        score = min(100, (raw_score / max_expected_score) * 100)
        
        return score
    
    def _analyze_activity_pattern(self, group: pd.DataFrame) -> Dict:
        """Analyze when the author is most active."""
        if 'created_at' not in group.columns:
            return {'primary_hours': [], 'primary_days': []}
        
        dates = pd.to_datetime(group['created_at'], format='ISO8601', errors='coerce')
        dates = dates.dropna()
        
        if len(dates) == 0:
            return {'primary_hours': [], 'primary_days': []}
        
        hours = dates.dt.hour
        days = dates.dt.dayofweek
        
        # Most common hours (top 3)
        hour_counts = hours.value_counts()
        top_hours = hour_counts.head(3).index.tolist()
        
        # Most common days
        day_names = {0: 'Pazartesi', 1: 'Salı', 2: 'Çarşamba', 
                     3: 'Perşembe', 4: 'Cuma', 5: 'Cumartesi', 6: 'Pazar'}
        day_counts = days.value_counts()
        top_days = [day_names.get(d, str(d)) for d in day_counts.head(2).index.tolist()]
        
        # Classify activity type
        if len(top_hours) > 0:
            avg_hour = np.mean(top_hours)
            if 6 <= avg_hour < 12:
                time_type = 'morning_person'
                time_label = 'Sabahçı'
            elif 12 <= avg_hour < 18:
                time_type = 'afternoon_person'
                time_label = 'Öğlenci'
            elif 18 <= avg_hour < 24:
                time_type = 'evening_person'
                time_label = 'Akşamcı'
            else:
                time_type = 'night_owl'
                time_label = 'Gece Kuşu'
        else:
            time_type = 'unknown'
            time_label = 'Bilinmiyor'
        
        return {
            'primary_hours': [int(h) for h in top_hours],
            'primary_days': top_days,
            'time_type': time_type,
            'time_label': time_label,
        }
    
    def _analyze_content_style(self, group: pd.DataFrame) -> Dict:
        """Analyze author's content style."""
        if 'content' not in group.columns and 'cleaned_text' not in group.columns:
            return {'avg_length': 0, 'style_type': 'unknown'}
        
        text_col = 'cleaned_text' if 'cleaned_text' in group.columns else 'content'
        texts = group[text_col].fillna('')
        
        # Average text length
        avg_length = texts.str.len().mean()
        
        # Count URLs, mentions, hashtags
        url_count = texts.str.count(r'https?://').sum()
        mention_count = texts.str.count(r'@\w+').sum()
        hashtag_count = texts.str.count(r'#\w+').sum()
        
        post_count = len(group)
        
        # Classify style
        if url_count / post_count > 0.5:
            style_type = 'link_sharer'
            style_label = 'Link Paylaşımcı'
        elif mention_count / post_count > 1:
            style_type = 'conversationalist'
            style_label = 'Sohbetçi'
        elif hashtag_count / post_count > 2:
            style_type = 'hashtag_user'
            style_label = 'Hashtag Kullanıcısı'
        elif avg_length > 200:
            style_type = 'long_form'
            style_label = 'Uzun İçerik'
        else:
            style_type = 'regular'
            style_label = 'Normal'
        
        return {
            'avg_length': round(avg_length, 1),
            'urls_per_post': round(url_count / post_count, 2),
            'mentions_per_post': round(mention_count / post_count, 2),
            'hashtags_per_post': round(hashtag_count / post_count, 2),
            'style_type': style_type,
            'style_label': style_label,
        }
    
    def _extract_topics(self, group: pd.DataFrame) -> List[str]:
        """Extract author's main topics from hashtags."""
        # Check multiple possible text columns
        text_col = None
        for col in ['cleaned_text', 'content', 'text']:
            if col in group.columns:
                text_col = col
                break
        
        if text_col is None:
            return []
        
        all_hashtags = []
        for content in group[text_col].fillna(''):
            hashtags = re.findall(r'#(\w+)', str(content).lower())
            all_hashtags.extend(hashtags)
        
        # Get top 5 hashtags
        hashtag_counts = Counter(all_hashtags)
        return [tag for tag, _ in hashtag_counts.most_common(5)]
    
    def _calculate_summary_stats(self, profiles: List[Dict]) -> Dict:
        """Calculate summary statistics across all profiles."""
        if not profiles:
            return {}
        
        influence_scores = [p['influence_score'] for p in profiles]
        post_counts = [p['post_count'] for p in profiles]
        
        return {
            'avg_influence_score': round(np.mean(influence_scores), 2),
            'median_influence_score': round(np.median(influence_scores), 2),
            'avg_posts_per_author': round(np.mean(post_counts), 2),
            'total_posts_analyzed': sum(post_counts),
        }
    
    def _categorize_authors(self, profiles: List[Dict]) -> Dict:
        """Categorize authors by influence level."""
        if not profiles:
            return {}
        
        categories = {
            'high_influence': [],
            'medium_influence': [],
            'low_influence': [],
        }
        
        for profile in profiles:
            score = profile['influence_score']
            author = profile['author']
            
            if score >= 50:
                categories['high_influence'].append(author)
            elif score >= 20:
                categories['medium_influence'].append(author)
            else:
                categories['low_influence'].append(author)
        
        return {
            'Yüksek Etki': len(categories['high_influence']),
            'Orta Etki': len(categories['medium_influence']),
            'Düşük Etki': len(categories['low_influence']),
        }


def profile_authors(df: pd.DataFrame, min_posts: int = 2) -> Dict:
    """
    Convenience function to profile authors.
    
    Args:
        df: DataFrame with author data
        min_posts: Minimum posts required
        
    Returns:
        Author profiling results
    """
    profiler = AuthorProfiler(min_posts=min_posts)
    return profiler.profile_authors(df)


def get_author_summary(results: Dict) -> str:
    """Generate text summary of author profiling."""
    lines = ["👤 Yazar Profili Özeti", "=" * 40]
    
    lines.append(f"\n📊 Genel İstatistikler:")
    lines.append(f"  • Toplam yazar: {results.get('total_authors', 0)}")
    lines.append(f"  • Profil oluşturulan: {results.get('profiled_authors', 0)}")
    
    stats = results.get('summary_stats', {})
    lines.append(f"  • Ortalama etki skoru: {stats.get('avg_influence_score', 0)}")
    
    # Top influencers
    top = results.get('top_influencers', [])[:5]
    if top:
        lines.append(f"\n⭐ En Etkili Yazarlar:")
        for i, profile in enumerate(top, 1):
            lines.append(f"  {i}. @{profile['author']}: {profile['influence_score']} puan")
    
    # Categories
    categories = results.get('author_categories', {})
    if categories:
        lines.append(f"\n📈 Etki Kategorileri:")
        for cat, count in categories.items():
            lines.append(f"  • {cat}: {count} yazar")
    
    return "\n".join(lines)


