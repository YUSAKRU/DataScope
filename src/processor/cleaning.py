"""
Data cleaning module for DataScope.

This module provides functions for cleaning and preprocessing text data
collected from social media platforms.
"""

import re
from typing import List, Optional

import pandas as pd
from bs4 import BeautifulSoup

from ..utils.exceptions import MissingColumnError
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Required columns for processing
REQUIRED_COLUMNS = ['id', 'text', 'author', 'created_at']

# Turkish stopwords (common words to filter out)
TURKISH_STOPWORDS = {
    'bir', 'bu', 've', 'de', 'da', 'için', 'ile', 'ama', 'ancak', 'çok',
    'daha', 'en', 'gibi', 'her', 'hem', 'hiç', 'kadar', 'mı', 'mi', 'mu',
    'mü', 'ne', 'neden', 'niçin', 'o', 'olan', 'olarak', 'onu', 'şu',
    'var', 'ya', 'yani', 'ki', 'ben', 'sen', 'biz', 'siz', 'onlar',
    'benim', 'senin', 'onun', 'bizim', 'sizin', 'onların', 'bu', 'şu',
    'bunlar', 'şunlar', 'bunu', 'şunu', 'bunları', 'şunları', 'oldu',
    'olan', 'olmuş', 'olacak', 'olmak', 'değil', 'ise', 'olup', 'olur',
    'olduğu', 'olduğunu', 'olması', 'etmek', 'etti', 'etmiş', 'edecek',
    'edildi', 'edilmiş', 'edilecek', 'yapmak', 'yaptı', 'yapmış', 'yapacak',
    'yapıldı', 'yapılmış', 'yapılacak', 'demek', 'dedi', 'demiş', 'diyecek',
    'söylemek', 'söyledi', 'söylemiş', 'söyleyecek', 'almak', 'aldı',
    'almış', 'alacak', 'vermek', 'verdi', 'vermiş', 'verecek', 'gelmek',
    'geldi', 'gelmiş', 'gelecek', 'gitmek', 'gitti', 'gitmiş', 'gidecek',
    'görmek', 'gördü', 'görmüş', 'görecek', 'bilmek', 'bildi', 'bilmiş',
    'bilecek', 'istemek', 'istedi', 'istemiş', 'isteyecek', 'başlamak',
    'başladı', 'başlamış', 'başlayacak', 'çalışmak', 'çalıştı', 'çalışmış',
    'çalışacak', 'geçmek', 'geçti', 'geçmiş', 'geçecek', 'kalmak', 'kaldı',
    'kalmış', 'kalacak', 'çıkmak', 'çıktı', 'çıkmış', 'çıkacak', 'düşünmek',
    'düşündü', 'düşünmüş', 'düşünecek', 'bulunmak', 'bulundu', 'bulunmuş',
    'bulunacak', 'orada', 'burada', 'şurada', 'nerede', 'şimdi', 'sonra',
    'önce', 'hep', 'hiçbir', 'herhangi', 'bazı', 'birkaç', 'birçok', 'tüm',
    'bütün', 'hepsi', 'diğer', 'başka', 'aynı', 'kendi', 'sadece', 'yalnız',
    'bile', 'dahi', 'üzere', 'rağmen', 'karşı', 'göre', 'doğru', 'arasında',
    'içinde', 'dışında', 'üzerinde', 'altında', 'yanında', 'arkasında',
    'önünde', 'tarafından', 'hakkında', 'üzerine', 'dolayı', 'nedeniyle',
    'sayesinde', 'yüzünden', 'itibaren', 'kadar', 'boyunca', 'süresince',
    'esnasında', 'sırasında', 'zarfında', 'özellikle', 'genellikle',
    'önceden', 'sonradan', 'yakında', 'uzakta', 'aşağıda', 'yukarıda',
    'içeride', 'dışarıda', 'buralarda', 'oralarda', 'herkes', 'kimse',
    'hiç', 'hiçbir', 'http', 'https', 'www', 'com', 'org', 'net', 'tr',
    'rt', 'via', 'cc',
}


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: HTML containing text
        
    Returns:
        str: Cleaned text without HTML tags
        
    Example:
        >>> clean_html("<p>Merhaba <b>dünya</b></p>")
        "Merhaba dünya"
    """
    if not text:
        return ""
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(text, 'lxml')
    
    # Replace <br> tags with newlines
    for br in soup.find_all('br'):
        br.replace_with('\n')
    
    # Replace <p> tags with newlines
    for p in soup.find_all('p'):
        p.insert_after('\n')
    
    # Get plain text
    cleaned = soup.get_text()
    
    return cleaned


def clean_urls(text: str) -> str:
    """
    Remove URLs from text.
    
    Args:
        text: Text containing URLs
        
    Returns:
        str: Text without URLs
        
    Example:
        >>> clean_urls("Check this https://example.com out")
        "Check this  out"
    """
    if not text:
        return ""
    
    # Pattern to match URLs
    url_pattern = r'https?://\S+|www\.\S+'
    cleaned = re.sub(url_pattern, '', text)
    
    return cleaned


def clean_mentions(text: str) -> str:
    """
    Remove @mentions from text.
    
    Args:
        text: Text containing mentions
        
    Returns:
        str: Text without mentions
        
    Example:
        >>> clean_mentions("Hello @user how are you")
        "Hello  how are you"
    """
    if not text:
        return ""
    
    # Pattern to match mentions (@username or @user@instance.com)
    mention_pattern = r'@[\w.-]+(?:@[\w.-]+)?'
    cleaned = re.sub(mention_pattern, '', text)
    
    return cleaned


def clean_hashtags(text: str, keep_word: bool = True) -> str:
    """
    Remove or clean hashtags from text.
    
    Args:
        text: Text containing hashtags
        keep_word: If True, keep the word but remove # symbol
                   If False, remove the entire hashtag
        
    Returns:
        str: Cleaned text
        
    Example:
        >>> clean_hashtags("#iklim değişikliği #önemli", keep_word=True)
        "iklim değişikliği önemli"
        >>> clean_hashtags("#iklim değişikliği #önemli", keep_word=False)
        "değişikliği"
    """
    if not text:
        return ""
    
    if keep_word:
        # Just remove the # symbol
        cleaned = re.sub(r'#(\w+)', r'\1', text)
    else:
        # Remove entire hashtag
        cleaned = re.sub(r'#\w+', '', text)
    
    return cleaned


def clean_special_characters(text: str, keep_punctuation: bool = True) -> str:
    """
    Remove special characters from text.
    
    Args:
        text: Text with special characters
        keep_punctuation: If True, keep basic punctuation marks
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    if keep_punctuation:
        # Keep letters, numbers, spaces, and basic punctuation
        # Also keep Turkish special characters
        cleaned = re.sub(r'[^\w\s.,!?;:\'"()\-çğıöşüÇĞİÖŞÜ]', '', text)
    else:
        # Keep only letters, numbers, and spaces
        cleaned = re.sub(r'[^\w\s]', '', text)
    
    return cleaned


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    - Multiple spaces become single space
    - Multiple newlines become single newline
    - Leading/trailing whitespace removed
    
    Args:
        text: Text with irregular whitespace
        
    Returns:
        str: Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple spaces with single space
    cleaned = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with single newline
    cleaned = re.sub(r'\n+', '\n', cleaned)
    
    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned


def clean_text(text: str) -> str:
    """
    Clean text by applying all cleaning operations.
    
    Args:
        text: Raw text
        
    Returns:
        str: Cleaned text
        
    Operations:
        1. Remove HTML tags
        2. Remove URLs
        3. Remove @mentions
        4. Clean hashtags (keep words)
        5. Remove special characters
        6. Normalize whitespace
        
    Example:
        >>> raw = "<p>@user check https://example.com #iklim değişikliği!</p>"
        >>> clean_text(raw)
        "check iklim değişikliği!"
    """
    if not text:
        return ""
    
    # Apply cleaning steps in order
    cleaned = clean_html(text)
    cleaned = clean_urls(cleaned)
    cleaned = clean_mentions(cleaned)
    cleaned = clean_hashtags(cleaned, keep_word=True)
    cleaned = clean_special_characters(cleaned, keep_punctuation=True)
    cleaned = normalize_whitespace(cleaned)
    
    return cleaned


def remove_stopwords(text: str, stopwords: Optional[set] = None) -> str:
    """
    Remove stopwords from text.
    
    Args:
        text: Input text
        stopwords: Set of stopwords to remove (default: Turkish stopwords)
        
    Returns:
        str: Text without stopwords
    """
    if not text:
        return ""
    
    if stopwords is None:
        stopwords = TURKISH_STOPWORDS
    
    words = text.lower().split()
    filtered_words = [word for word in words if word not in stopwords]
    
    return ' '.join(filtered_words)


def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validate that DataFrame has required columns.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        MissingColumnError: If a required column is missing
    """
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            raise MissingColumnError(column, REQUIRED_COLUMNS)


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process DataFrame by cleaning all text content.
    
    Args:
        df: Raw data DataFrame
            Required columns: ['id', 'text', 'author', 'created_at']
            
    Returns:
        pd.DataFrame: Cleaned DataFrame with additional column:
            - cleaned_text: Cleaned version of text
            
    Raises:
        MissingColumnError: If a required column is missing
        
    Example:
        >>> df = pd.DataFrame({'id': [1], 'text': ['<p>Hello!</p>'], 
        ...                    'author': ['user'], 'created_at': ['2024-01-01']})
        >>> df = process_dataframe(df)
        >>> print(df['cleaned_text'][0])
        "Hello!"
    """
    # Validate required columns
    validate_dataframe(df)
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    logger.info(f"Processing {len(df)} posts...")
    
    # Apply text cleaning
    df['cleaned_text'] = df['text'].apply(clean_text)
    
    # Remove empty cleaned texts
    empty_count = (df['cleaned_text'] == '').sum()
    if empty_count > 0:
        logger.warning(f"Found {empty_count} posts with empty cleaned text")
    
    # Add text length column for analysis
    df['text_length'] = df['cleaned_text'].str.len()
    
    logger.info(f"Processing complete. {len(df)} posts processed.")
    
    return df


def get_word_frequencies(texts: List[str], stopwords: Optional[set] = None) -> dict:
    """
    Get word frequencies from a list of texts.
    
    Args:
        texts: List of text strings
        stopwords: Set of stopwords to exclude
        
    Returns:
        dict: Word frequencies {word: count}
    """
    if stopwords is None:
        stopwords = TURKISH_STOPWORDS
    
    word_counts = {}
    
    for text in texts:
        if not text:
            continue
        
        # Tokenize and clean
        words = text.lower().split()
        
        for word in words:
            # Skip stopwords and short words
            if word in stopwords or len(word) < 2:
                continue
            
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency
    sorted_counts = dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True))
    
    return sorted_counts


