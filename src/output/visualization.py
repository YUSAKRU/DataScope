"""
Visualization module for DataScope.

This module provides functions for creating visualizations of analysis results,
including sentiment distribution charts, word clouds, and time series plots.
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from wordcloud import WordCloud

from ..utils.logger import get_logger
from ..processor.cleaning import TURKISH_STOPWORDS, get_word_frequencies

logger = get_logger(__name__)

# Set matplotlib to use a font that supports Turkish characters
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# Color palette for sentiment
SENTIMENT_COLORS = {
    'positive': '#2ecc71',  # Green
    'negative': '#e74c3c',  # Red
    'neutral': '#95a5a6',   # Gray
}

# Turkish labels
SENTIMENT_LABELS_TR = {
    'positive': 'Pozitif',
    'negative': 'Negatif',
    'neutral': 'Nötr',
}


def create_sentiment_distribution(
    df: pd.DataFrame, 
    output_path: str,
    title: str = "Duygu Dağılımı"
) -> None:
    """
    Create a sentiment distribution pie chart.
    
    Args:
        df: DataFrame with sentiment_label column
        output_path: Output file path (PNG)
        title: Chart title (default: "Duygu Dağılımı")
        
    Output:
        Pie chart showing positive, negative, and neutral percentages
        with Turkish labels.
    """
    if 'sentiment_label' not in df.columns:
        raise ValueError("DataFrame must have 'sentiment_label' column")
    
    # Count sentiments
    sentiment_counts = df['sentiment_label'].value_counts()
    
    # Prepare data in order
    labels = []
    sizes = []
    colors = []
    
    for sentiment in ['positive', 'negative', 'neutral']:
        if sentiment in sentiment_counts.index:
            labels.append(SENTIMENT_LABELS_TR[sentiment])
            sizes.append(sentiment_counts[sentiment])
            colors.append(SENTIMENT_COLORS[sentiment])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        explode=[0.02] * len(sizes),
        shadow=True,
    )
    
    # Style the text
    for text in texts:
        text.set_fontsize(14)
        text.set_fontweight('bold')
    
    for autotext in autotexts:
        autotext.set_fontsize(12)
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Add legend with counts
    legend_labels = [f"{label}: {count}" for label, count in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, title="Toplam", loc="center left", 
              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=11)
    
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    logger.info(f"Sentiment distribution chart saved to: {output_path}")


def create_wordcloud(
    df: pd.DataFrame, 
    output_path: str,
    text_column: str = 'cleaned_text',
    max_words: int = 200,
    background_color: str = 'white',
    width: int = 1200,
    height: int = 600
) -> None:
    """
    Create a word cloud from text data.
    
    Args:
        df: DataFrame with text column
        output_path: Output file path (PNG)
        text_column: Name of the text column (default: 'cleaned_text')
        max_words: Maximum number of words (default: 200)
        background_color: Background color (default: 'white')
        width: Image width in pixels (default: 1200)
        height: Image height in pixels (default: 600)
        
    Features:
        - Turkish character support
        - Stopword filtering
    """
    if text_column not in df.columns:
        raise ValueError(f"DataFrame must have '{text_column}' column")
    
    # Combine all texts
    all_text = ' '.join(df[text_column].fillna('').astype(str))
    
    if not all_text.strip():
        logger.warning("No text content for word cloud")
        return
    
    # Create word cloud
    wordcloud = WordCloud(
        width=width,
        height=height,
        max_words=max_words,
        background_color=background_color,
        stopwords=TURKISH_STOPWORDS,
        font_path=None,  # Use default font
        colormap='viridis',
        collocations=False,
        min_font_size=10,
        max_font_size=150,
    ).generate(all_text)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('Kelime Bulutu', fontsize=16, fontweight='bold', pad=10)
    
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    logger.info(f"Word cloud saved to: {output_path}")


def create_time_series(
    df: pd.DataFrame, 
    output_path: str,
    date_column: str = 'created_at',
    score_column: str = 'sentiment_score'
) -> None:
    """
    Create a time series chart of sentiment over time.
    
    Args:
        df: DataFrame with date and sentiment columns
        output_path: Output file path (PNG)
        date_column: Name of the date column (default: 'created_at')
        score_column: Name of the sentiment score column (default: 'sentiment_score')
    """
    required_cols = [date_column, score_column]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"DataFrame must have '{col}' column")
    
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    df['date'] = df[date_column].dt.date
    
    # Aggregate by date
    daily_data = df.groupby('date').agg({
        score_column: 'mean',
        'id': 'count'
    }).rename(columns={'id': 'count'}).reset_index()
    
    daily_data['date'] = pd.to_datetime(daily_data['date'])
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # Subplot 1: Sentiment score over time
    ax1.plot(daily_data['date'], daily_data[score_column], 
             color='#3498db', linewidth=2, marker='o', markersize=4)
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.axhline(y=0.25, color='green', linestyle=':', alpha=0.5, label='Pozitif eşik')
    ax1.axhline(y=-0.25, color='red', linestyle=':', alpha=0.5, label='Negatif eşik')
    ax1.fill_between(daily_data['date'], daily_data[score_column], 0, 
                     where=daily_data[score_column] >= 0, alpha=0.3, color='green')
    ax1.fill_between(daily_data['date'], daily_data[score_column], 0, 
                     where=daily_data[score_column] < 0, alpha=0.3, color='red')
    ax1.set_ylabel('Ortalama Duygu Skoru', fontsize=12)
    ax1.set_title('Zaman İçinde Duygu Değişimi', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Post count over time
    ax2.bar(daily_data['date'], daily_data['count'], color='#9b59b6', alpha=0.7)
    ax2.set_xlabel('Tarih', fontsize=12)
    ax2.set_ylabel('Gönderi Sayısı', fontsize=12)
    ax2.set_title('Günlük Gönderi Sayısı', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis dates
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    logger.info(f"Time series chart saved to: {output_path}")


def create_sentiment_by_author(
    df: pd.DataFrame, 
    output_path: str,
    top_n: int = 15
) -> None:
    """
    Create a chart showing sentiment distribution by top authors.
    
    Args:
        df: DataFrame with author and sentiment columns
        output_path: Output file path (PNG)
        top_n: Number of top authors to include (default: 15)
    """
    if 'author' not in df.columns or 'sentiment_label' not in df.columns:
        raise ValueError("DataFrame must have 'author' and 'sentiment_label' columns")
    
    # Get top authors by post count
    top_authors = df['author'].value_counts().head(top_n).index.tolist()
    
    # Filter to top authors
    df_top = df[df['author'].isin(top_authors)].copy()
    
    # Create pivot table
    pivot = pd.crosstab(df_top['author'], df_top['sentiment_label'])
    pivot = pivot.reindex(top_authors)  # Keep order
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = [SENTIMENT_COLORS.get(col, '#cccccc') for col in pivot.columns]
    pivot.plot(kind='barh', stacked=True, ax=ax, color=colors)
    
    ax.set_xlabel('Gönderi Sayısı', fontsize=12)
    ax.set_ylabel('Yazar', fontsize=12)
    ax.set_title('Yazarlara Göre Duygu Dağılımı', fontsize=14, fontweight='bold')
    
    # Rename legend labels to Turkish
    handles, labels = ax.get_legend_handles_labels()
    labels = [SENTIMENT_LABELS_TR.get(label, label) for label in labels]
    ax.legend(handles, labels, title='Duygu', loc='lower right')
    
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    logger.info(f"Sentiment by author chart saved to: {output_path}")


def create_engagement_distribution(
    df: pd.DataFrame, 
    output_path: str
) -> None:
    """
    Create a chart showing engagement distribution.
    
    Args:
        df: DataFrame with engagement columns
        output_path: Output file path (PNG)
    """
    engagement_cols = ['reblogs_count', 'favourites_count', 'replies_count']
    existing_cols = [col for col in engagement_cols if col in df.columns]
    
    if not existing_cols:
        raise ValueError("No engagement columns found")
    
    # Prepare data
    fig, axes = plt.subplots(1, len(existing_cols), figsize=(5 * len(existing_cols), 5))
    
    if len(existing_cols) == 1:
        axes = [axes]
    
    col_names_tr = {
        'reblogs_count': 'Reblog',
        'favourites_count': 'Favori',
        'replies_count': 'Yanıt',
    }
    
    for ax, col in zip(axes, existing_cols):
        data = df[col].dropna()
        
        # Create histogram
        ax.hist(data, bins=30, color='#3498db', edgecolor='white', alpha=0.7)
        ax.set_xlabel(col_names_tr.get(col, col), fontsize=12)
        ax.set_ylabel('Frekans', fontsize=12)
        ax.set_title(f'{col_names_tr.get(col, col)} Dağılımı', fontsize=12, fontweight='bold')
        
        # Add mean line
        mean_val = data.mean()
        ax.axvline(mean_val, color='red', linestyle='--', label=f'Ortalama: {mean_val:.2f}')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('Etkileşim Dağılımları', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    logger.info(f"Engagement distribution chart saved to: {output_path}")


def create_all_visualizations(
    df: pd.DataFrame, 
    output_dir: str
) -> Dict[str, str]:
    """
    Create all available visualizations.
    
    Args:
        df: DataFrame with all required columns
        output_dir: Directory for output files
        
    Returns:
        Dict: Mapping of visualization names to file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    paths = {}
    
    # Sentiment distribution
    if 'sentiment_label' in df.columns:
        path = str(output_dir / 'sentiment_distribution.png')
        try:
            create_sentiment_distribution(df, path)
            paths['sentiment_distribution'] = path
        except Exception as e:
            logger.error(f"Failed to create sentiment distribution: {e}")
    
    # Word cloud
    if 'cleaned_text' in df.columns:
        path = str(output_dir / 'wordcloud.png')
        try:
            create_wordcloud(df, path)
            paths['wordcloud'] = path
        except Exception as e:
            logger.error(f"Failed to create word cloud: {e}")
    
    # Time series
    if 'sentiment_score' in df.columns and 'created_at' in df.columns:
        path = str(output_dir / 'time_series.png')
        try:
            create_time_series(df, path)
            paths['time_series'] = path
        except Exception as e:
            logger.error(f"Failed to create time series: {e}")
    
    # Sentiment by author
    if 'author' in df.columns and 'sentiment_label' in df.columns:
        path = str(output_dir / 'sentiment_by_author.png')
        try:
            create_sentiment_by_author(df, path)
            paths['sentiment_by_author'] = path
        except Exception as e:
            logger.error(f"Failed to create sentiment by author: {e}")
    
    # Engagement distribution
    if any(col in df.columns for col in ['reblogs_count', 'favourites_count', 'replies_count']):
        path = str(output_dir / 'engagement_distribution.png')
        try:
            create_engagement_distribution(df, path)
            paths['engagement_distribution'] = path
        except Exception as e:
            logger.error(f"Failed to create engagement distribution: {e}")
    
    logger.info(f"Created {len(paths)} visualizations in {output_dir}")
    
    return paths


