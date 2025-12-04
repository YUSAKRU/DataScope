"""
PDF report generation module for DataScope.

This module provides functions for creating PDF reports with Turkish
character support using ReportLab.
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..utils.logger import get_logger
from ..utils.exceptions import FontNotFoundError, FileWriteError

logger = get_logger(__name__)

# Font paths to try
FONT_PATHS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/TTF/DejaVuSans.ttf',
    '/System/Library/Fonts/Supplemental/DejaVu Sans.ttf',
    'C:/Windows/Fonts/DejaVuSans.ttf',
]

FONT_BOLD_PATHS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
    '/System/Library/Fonts/Supplemental/DejaVu Sans Bold.ttf',
    'C:/Windows/Fonts/DejaVuSans-Bold.ttf',
]


def _register_fonts() -> bool:
    """
    Register Turkish-compatible fonts.
    
    Returns:
        bool: True if fonts registered successfully
    """
    font_registered = False
    
    # Try to register regular font
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', path))
                font_registered = True
                logger.debug(f"Registered DejaVuSans from: {path}")
                break
            except Exception as e:
                logger.debug(f"Could not register font from {path}: {e}")
    
    # Try to register bold font
    for path in FONT_BOLD_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', path))
                logger.debug(f"Registered DejaVuSans-Bold from: {path}")
                break
            except Exception as e:
                logger.debug(f"Could not register bold font from {path}: {e}")
    
    return font_registered


def _get_styles() -> Dict[str, ParagraphStyle]:
    """
    Get paragraph styles for the report.
    
    Returns:
        Dict: Style name to ParagraphStyle mapping
    """
    # Register fonts
    font_name = 'DejaVuSans' if _register_fonts() else 'Helvetica'
    bold_font = 'DejaVuSans-Bold' if font_name == 'DejaVuSans' else 'Helvetica-Bold'
    
    styles = {
        'title': ParagraphStyle(
            'Title',
            fontName=bold_font,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
        ),
        'subtitle': ParagraphStyle(
            'Subtitle',
            fontName=font_name,
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#7f8c8d'),
        ),
        'heading1': ParagraphStyle(
            'Heading1',
            fontName=bold_font,
            fontSize=18,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#2980b9'),
        ),
        'heading2': ParagraphStyle(
            'Heading2',
            fontName=bold_font,
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#27ae60'),
        ),
        'body': ParagraphStyle(
            'Body',
            fontName=font_name,
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=16,
        ),
        'small': ParagraphStyle(
            'Small',
            fontName=font_name,
            fontSize=9,
            textColor=colors.HexColor('#95a5a6'),
        ),
        'stat_value': ParagraphStyle(
            'StatValue',
            fontName=bold_font,
            fontSize=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50'),
        ),
        'stat_label': ParagraphStyle(
            'StatLabel',
            fontName=font_name,
            fontSize=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#7f8c8d'),
        ),
    }
    
    return styles


def create_pdf_report(
    df: pd.DataFrame,
    stats: Dict[str, Any],
    graphs: Dict[str, str],
    output_path: str,
    title: str = "DataScope Analiz Raporu",
    hashtag: str = "",
    instance: str = ""
) -> None:
    """
    Create a PDF report with analysis results.
    
    Args:
        df: Analyzed DataFrame
        stats: Statistics dictionary from generate_full_report()
        graphs: Dictionary mapping graph names to file paths
        output_path: Output file path (PDF)
        title: Report title
        hashtag: Analyzed hashtag
        instance: Mastodon instance URL
        
    Features:
        - Turkish character support (DejaVu Sans font)
        - A4 page size
        - Embedded graphs
        - Formatted tables
    """
    logger.info(f"Creating PDF report: {output_path}")
    
    styles = _get_styles()
    
    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    
    story = []
    
    # Title
    story.append(Paragraph(title, styles['title']))
    
    # Subtitle with date and hashtag
    subtitle_text = f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    if hashtag:
        subtitle_text += f" | Hashtag: #{hashtag}"
    if instance:
        subtitle_text += f"<br/>Kaynak: {instance}"
    story.append(Paragraph(subtitle_text, styles['subtitle']))
    
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("1. Özet", styles['heading1']))
    
    basic_stats = stats.get('basic_stats', {})
    sentiment_stats = stats.get('sentiment_stats', {})
    
    summary_text = f"""
    Bu rapor, <b>#{hashtag}</b> hashtag'i için yapılan duygu analizi sonuçlarını içermektedir.
    Toplam <b>{basic_stats.get('total_posts', 0)}</b> gönderi analiz edilmiştir.
    Gönderiler <b>{basic_stats.get('unique_authors', 0)}</b> farklı yazar tarafından paylaşılmıştır.
    """
    story.append(Paragraph(summary_text, styles['body']))
    
    story.append(Spacer(1, 15))
    
    # Key Metrics Table
    if sentiment_stats:
        metrics_data = [
            ['Metrik', 'Değer'],
            ['Toplam Gönderi', str(basic_stats.get('total_posts', 0))],
            ['Analiz Edilen', str(sentiment_stats.get('total_analyzed', 0))],
            ['Pozitif', f"{sentiment_stats.get('positive_count', 0)} ({sentiment_stats.get('positive_percentage', 0):.1f}%)"],
            ['Negatif', f"{sentiment_stats.get('negative_count', 0)} ({sentiment_stats.get('negative_percentage', 0):.1f}%)"],
            ['Nötr', f"{sentiment_stats.get('neutral_count', 0)} ({sentiment_stats.get('neutral_percentage', 0):.1f}%)"],
        ]
        
        # Score stats if available
        score_stats = sentiment_stats.get('score_stats', {})
        if score_stats:
            metrics_data.append(['Ortalama Skor', f"{score_stats.get('mean', 0):.4f}"])
        
        metrics_table = Table(metrics_data, colWidths=[8*cm, 6*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        story.append(metrics_table)
    
    story.append(Spacer(1, 20))
    
    # Sentiment Distribution Chart
    if 'sentiment_distribution' in graphs:
        story.append(Paragraph("2. Duygu Dağılımı", styles['heading1']))
        story.append(Paragraph(
            "Aşağıdaki grafik, analiz edilen gönderilerin duygu dağılımını göstermektedir.",
            styles['body']
        ))
        
        try:
            img = Image(graphs['sentiment_distribution'], width=14*cm, height=11*cm)
            story.append(img)
        except Exception as e:
            logger.warning(f"Could not add sentiment distribution image: {e}")
        
        story.append(Spacer(1, 15))
    
    # Time Series Chart
    if 'time_series' in graphs:
        story.append(PageBreak())
        story.append(Paragraph("3. Zaman İçinde Duygu Değişimi", styles['heading1']))
        story.append(Paragraph(
            "Aşağıdaki grafik, duygu skorunun ve gönderi sayısının zaman içindeki değişimini göstermektedir.",
            styles['body']
        ))
        
        try:
            img = Image(graphs['time_series'], width=16*cm, height=11*cm)
            story.append(img)
        except Exception as e:
            logger.warning(f"Could not add time series image: {e}")
        
        story.append(Spacer(1, 15))
    
    # Word Cloud
    if 'wordcloud' in graphs:
        story.append(Paragraph("4. Kelime Bulutu", styles['heading1']))
        story.append(Paragraph(
            "Aşağıdaki kelime bulutu, gönderilerde en sık kullanılan kelimeleri göstermektedir.",
            styles['body']
        ))
        
        try:
            img = Image(graphs['wordcloud'], width=16*cm, height=8*cm)
            story.append(img)
        except Exception as e:
            logger.warning(f"Could not add word cloud image: {e}")
        
        story.append(Spacer(1, 15))
    
    # Top Words Table
    word_stats = stats.get('word_stats', {})
    if word_stats and 'top_words' in word_stats:
        story.append(Paragraph("5. En Sık Kullanılan Kelimeler", styles['heading1']))
        
        top_words = list(word_stats['top_words'].items())[:20]
        
        # Split into two columns
        mid = len(top_words) // 2
        left_words = top_words[:mid]
        right_words = top_words[mid:]
        
        words_data = [['Kelime', 'Sayı', 'Kelime', 'Sayı']]
        for i in range(max(len(left_words), len(right_words))):
            row = []
            if i < len(left_words):
                row.extend([left_words[i][0], str(left_words[i][1])])
            else:
                row.extend(['', ''])
            if i < len(right_words):
                row.extend([right_words[i][0], str(right_words[i][1])])
            else:
                row.extend(['', ''])
            words_data.append(row)
        
        words_table = Table(words_data, colWidths=[5*cm, 2.5*cm, 5*cm, 2.5*cm])
        words_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        story.append(words_table)
    
    story.append(Spacer(1, 20))
    
    # Author Statistics
    author_stats = stats.get('author_stats', {})
    if author_stats and 'top_authors_by_posts' in author_stats:
        story.append(PageBreak())
        story.append(Paragraph("6. Yazar İstatistikleri", styles['heading1']))
        
        story.append(Paragraph(
            f"Toplam {author_stats.get('unique_authors', 0)} farklı yazar katkıda bulunmuştur. "
            f"Yazar başına ortalama {author_stats.get('avg_posts_per_author', 0):.1f} gönderi düşmektedir.",
            styles['body']
        ))
        
        # Top authors table
        top_authors = list(author_stats['top_authors_by_posts'].items())[:10]
        authors_data = [['Sıra', 'Yazar', 'Gönderi Sayısı']]
        for i, (author, count) in enumerate(top_authors, 1):
            authors_data.append([str(i), author, str(count)])
        
        authors_table = Table(authors_data, colWidths=[2*cm, 8*cm, 4*cm])
        authors_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        story.append(authors_table)
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"Bu rapor DataScope v2.0 tarafından {datetime.now().strftime('%d.%m.%Y %H:%M')} tarihinde oluşturulmuştur.",
        styles['small']
    ))
    
    # Build PDF
    try:
        doc.build(story)
        logger.info(f"PDF report created successfully: {output_path}")
    except Exception as e:
        raise FileWriteError(output_path, str(e))


