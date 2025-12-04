"""
Text classification module for DataScope.

This module provides rule-based text classification
for categorizing social media posts by type.
"""

import re
from typing import Dict, List, Optional, Any
from collections import Counter

import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Classification patterns (Turkish)
PATTERNS = {
    'news': {
        'url_patterns': [
            r'https?://[^\s]+\.(com|net|org|gov|edu)',
        ],
        'keywords': [
            'son dakika', 'breaking', 'haber', 'duyuru', 'açıklama',
            'basın', 'bülteni', 'rapor', 'araştırma', 'yayınlandı',
            'açıklandı', 'bildirildi', 'kaynaklara göre',
        ],
        'weight': 1.0,
    },
    'opinion': {
        'first_person': [
            r'\bbence\b', r'\bbana göre\b', r'\bdüşünüyorum\b',
            r'\binanıyorum\b', r'\bkanımca\b', r'\bfikrimce\b',
            r'\bşahsen\b', r'\bkişisel olarak\b',
        ],
        'opinion_markers': [
            'katılıyorum', 'katılmıyorum', 'haklı', 'haksız',
            'destekliyorum', 'karşıyım', 'sevdim', 'beğendim',
            'harika', 'berbat', 'mükemmel', 'rezalet',
        ],
        'weight': 1.0,
    },
    'question': {
        'patterns': [
            r'\?$', r'\?[\s]*$',
            r'\bmi\b', r'\bmı\b', r'\bmu\b', r'\bmü\b',
            r'\bnasıl\b', r'\bneden\b', r'\bniçin\b', r'\bniye\b',
            r'\bne zaman\b', r'\bnerede\b', r'\bkim\b', r'\bhangisi\b',
            r'\bacaba\b', r'\bmerak\b',
        ],
        'weight': 1.0,
    },
    'call_to_action': {
        'patterns': [
            r'\bimzala\b', r'\bkatıl\b', r'\bdestek\s+ver\b',
            r'\bpaylaş\b', r'\byay\b', r'\bduyur\b',
            r'\brt\b', r'\bretweetle\b', r'\bboost\b',
            r'\bhemen\b', r'\bacil\b', r'\bönemli\b',
            r'\bharekete\s+geç\b', r'\bses\s+ver\b',
        ],
        'weight': 1.0,
    },
    'emotional': {
        'patterns': [
            r'[!]{2,}', r'[?!]{2,}', r'[\U0001F600-\U0001F64F]',
            r'[\U0001F300-\U0001F5FF]', r'[\U0001F680-\U0001F6FF]',
        ],
        'keywords': [
            'çok üzgün', 'çok mutlu', 'harika', 'korkunç',
            'inanılmaz', 'şok', 'dehşet', 'müthiş', 'muhteşem',
            'skandal', 'ayıp', 'yazık', 'bravo', 'helal',
        ],
        'weight': 0.8,
    },
    'informative': {
        'patterns': [
            r'\d+\s*(yıl|ay|gün|saat|dakika|%|tl|dolar|euro)',
            r'\d{4}', r'\d+\.\d+',
        ],
        'keywords': [
            'istatistik', 'veri', 'rakam', 'oran', 'yüzde',
            'artış', 'azalış', 'değişim', 'sonuç', 'toplam',
        ],
        'weight': 0.9,
    },
}


class TextClassifier:
    """
    Classify text into predefined categories.
    
    Categories:
    - news: News/link sharing
    - opinion: Personal opinions
    - question: Questions
    - call_to_action: Calls to action
    - emotional: Emotional content
    - informative: Data/statistics sharing
    - other: Unclassified
    
    Example:
        >>> classifier = TextClassifier()
        >>> result = classifier.classify("Bu konuda ne düşünüyorsunuz?")
        >>> print(result['category'])  # 'question'
    """
    
    def __init__(self, threshold: float = 0.3):
        """
        Initialize classifier.
        
        Args:
            threshold: Minimum score for classification
        """
        self.threshold = threshold
        self.patterns = PATTERNS
        
        # Compile regex patterns
        self._compiled_patterns = {}
        for category, rules in self.patterns.items():
            compiled = []
            for key in ['patterns', 'url_patterns', 'first_person']:
                if key in rules:
                    for pattern in rules[key]:
                        try:
                            compiled.append(re.compile(pattern, re.IGNORECASE))
                        except re.error:
                            logger.warning(f"Invalid regex pattern: {pattern}")
            self._compiled_patterns[category] = compiled
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify a single text.
        
        Args:
            text: Text to classify
            
        Returns:
            Classification result with category and confidence
        """
        if not text or not text.strip():
            return {
                'category': 'other',
                'category_label': 'Diğer',
                'confidence': 0.0,
                'scores': {},
            }
        
        text_lower = text.lower()
        scores = {}
        
        for category, rules in self.patterns.items():
            score = 0.0
            matches = 0
            
            # Check compiled patterns
            for pattern in self._compiled_patterns.get(category, []):
                if pattern.search(text_lower):
                    score += 0.3
                    matches += 1
            
            # Check keywords
            keywords = rules.get('keywords', []) + rules.get('opinion_markers', [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 0.2
                    matches += 1
            
            # Apply weight
            weight = rules.get('weight', 1.0)
            scores[category] = min(1.0, score * weight)
        
        # Find best category
        if scores:
            best_category = max(scores, key=scores.get)
            best_score = scores[best_category]
            
            if best_score >= self.threshold:
                return {
                    'category': best_category,
                    'category_label': self._get_label(best_category),
                    'confidence': round(best_score, 2),
                    'scores': {k: round(v, 2) for k, v in scores.items()},
                }
        
        return {
            'category': 'other',
            'category_label': 'Diğer',
            'confidence': 0.0,
            'scores': {k: round(v, 2) for k, v in scores.items()},
        }
    
    def _get_label(self, category: str) -> str:
        """Get Turkish label for category."""
        labels = {
            'news': 'Haber/Link Paylaşımı',
            'opinion': 'Kişisel Görüş',
            'question': 'Soru',
            'call_to_action': 'Eylem Çağrısı',
            'emotional': 'Duygusal İçerik',
            'informative': 'Bilgilendirici',
            'other': 'Diğer',
        }
        return labels.get(category, category)
    
    def classify_batch(self, texts: List[str]) -> List[Dict]:
        """
        Classify multiple texts.
        
        Args:
            texts: List of texts
            
        Returns:
            List of classification results
        """
        results = []
        for text in texts:
            results.append(self.classify(text))
        return results


def classify_texts(df: pd.DataFrame, text_column: str = 'cleaned_text') -> Dict[str, Any]:
    """
    Classify texts in a DataFrame.
    
    Args:
        df: DataFrame with text data
        text_column: Column containing text
        
    Returns:
        Classification results with distribution
    """
    if text_column not in df.columns:
        # Try alternative columns
        for alt in ['cleaned_text', 'content', 'text']:
            if alt in df.columns:
                text_column = alt
                break
        else:
            return {'error': f"Text column not found"}
    
    classifier = TextClassifier()
    texts = df[text_column].fillna('').tolist()
    
    results = classifier.classify_batch(texts)
    
    # Calculate distribution
    categories = [r['category'] for r in results]
    category_counts = Counter(categories)
    
    total = len(categories)
    distribution = {
        classifier._get_label(cat): {
            'count': count,
            'percentage': round(count / total * 100, 1)
        }
        for cat, count in category_counts.items()
    }
    
    # Sort by count
    distribution = dict(sorted(
        distribution.items(), 
        key=lambda x: x[1]['count'], 
        reverse=True
    ))
    
    # Find examples for each category
    examples = {}
    for cat in set(categories):
        cat_indices = [i for i, r in enumerate(results) if r['category'] == cat]
        if cat_indices:
            idx = cat_indices[0]
            examples[classifier._get_label(cat)] = {
                'text': texts[idx][:200] + '...' if len(texts[idx]) > 200 else texts[idx],
                'confidence': results[idx]['confidence'],
            }
    
    logger.info(f"Classified {len(texts)} texts into {len(category_counts)} categories")
    
    return {
        'classifications': results,
        'distribution': distribution,
        'examples': examples,
        'total_classified': len(texts),
        'category_counts': dict(category_counts),
    }


def get_classification_summary(results: Dict) -> str:
    """Generate text summary of classification results."""
    lines = ["📋 Metin Sınıflandırma Özeti", "=" * 40]
    
    lines.append(f"\n📊 Toplam: {results.get('total_classified', 0)} metin")
    
    distribution = results.get('distribution', {})
    if distribution:
        lines.append(f"\n📈 Kategori Dağılımı:")
        for cat, stats in distribution.items():
            bar = '█' * int(stats['percentage'] / 5)
            lines.append(f"  • {cat}: {stats['count']} ({stats['percentage']}%) {bar}")
    
    examples = results.get('examples', {})
    if examples:
        lines.append(f"\n📝 Örnek Metinler:")
        for cat, ex in list(examples.items())[:3]:
            lines.append(f"\n  [{cat}]")
            lines.append(f"  \"{ex['text'][:100]}...\"")
    
    return "\n".join(lines)


# Category descriptions for UI
CATEGORY_DESCRIPTIONS = {
    'news': 'Haber linkleri, basın bültenleri veya resmi duyuruları içeren paylaşımlar',
    'opinion': 'Kişisel görüş, yorum veya değerlendirme içeren paylaşımlar',
    'question': 'Soru soran veya bilgi talep eden paylaşımlar',
    'call_to_action': 'Paylaşım, imza veya katılım çağrısı yapan paylaşımlar',
    'emotional': 'Yoğun duygu ifadesi içeren paylaşımlar',
    'informative': 'İstatistik, veri veya somut bilgi içeren paylaşımlar',
    'other': 'Diğer kategorilere uymayan paylaşımlar',
}


