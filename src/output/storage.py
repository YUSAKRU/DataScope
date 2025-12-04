"""
Data storage module for DataScope.

This module provides functions for saving data to various formats
including CSV, JSON, and Excel.
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

import pandas as pd

from ..utils.logger import get_logger
from ..utils.exceptions import FileWriteError

logger = get_logger(__name__)


def save_to_csv(
    df: pd.DataFrame, 
    output_path: str,
    include_index: bool = False,
    encoding: str = 'utf-8-sig'  # UTF-8 with BOM for Excel compatibility
) -> str:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Output file path
        include_index: Whether to include row index (default: False)
        encoding: File encoding (default: utf-8-sig for Excel compatibility)
        
    Returns:
        str: Path to saved file
        
    Raises:
        FileWriteError: If file cannot be written
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=include_index, encoding=encoding)
        
        logger.info(f"Saved {len(df)} rows to CSV: {output_path}")
        return str(output_path)
        
    except Exception as e:
        raise FileWriteError(str(output_path), str(e))


def save_to_json(
    data: Any, 
    output_path: str,
    indent: int = 2,
    ensure_ascii: bool = False
) -> str:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save (dict, list, or DataFrame)
        output_path: Output file path
        indent: JSON indentation (default: 2)
        ensure_ascii: Whether to escape non-ASCII characters (default: False)
        
    Returns:
        str: Path to saved file
        
    Raises:
        FileWriteError: If file cannot be written
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert DataFrame to dict if needed
        if isinstance(data, pd.DataFrame):
            data = data.to_dict(orient='records')
        
        # Handle special objects
        def json_serializer(obj):
            import numpy as np
            from datetime import date, time
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, date):
                return obj.isoformat()
            if isinstance(obj, time):
                return obj.isoformat()
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, pd.Categorical):
                return str(obj)
            if pd.isna(obj):
                return None
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=json_serializer)
        
        logger.info(f"Saved data to JSON: {output_path}")
        return str(output_path)
        
    except Exception as e:
        raise FileWriteError(str(output_path), str(e))


def save_to_excel(
    df: pd.DataFrame, 
    output_path: str,
    sheet_name: str = 'Data',
    include_index: bool = False
) -> str:
    """
    Save DataFrame to Excel file.
    
    Args:
        df: DataFrame to save
        output_path: Output file path
        sheet_name: Name of the sheet (default: 'Data')
        include_index: Whether to include row index (default: False)
        
    Returns:
        str: Path to saved file
        
    Raises:
        FileWriteError: If file cannot be written
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_excel(output_path, sheet_name=sheet_name, index=include_index)
        
        logger.info(f"Saved {len(df)} rows to Excel: {output_path}")
        return str(output_path)
        
    except Exception as e:
        raise FileWriteError(str(output_path), str(e))


def save_analysis_results(
    df: pd.DataFrame,
    stats: Dict[str, Any],
    output_dir: str,
    prefix: str = "",
    formats: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Save all analysis results to multiple formats.
    
    Args:
        df: Analyzed DataFrame
        stats: Statistics dictionary
        output_dir: Output directory
        prefix: Filename prefix (optional)
        formats: List of formats to save ('csv', 'json', 'excel')
                 Default: ['csv', 'json']
        
    Returns:
        Dict: Mapping of format to file path
    """
    if formats is None:
        formats = ['csv', 'json']
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if prefix:
        base_name = f"{prefix}_{timestamp}"
    else:
        base_name = f"analysis_{timestamp}"
    
    saved_files = {}
    
    # Save DataFrame
    if 'csv' in formats:
        csv_path = output_dir / f"{base_name}_data.csv"
        saved_files['data_csv'] = save_to_csv(df, str(csv_path))
    
    if 'excel' in formats:
        excel_path = output_dir / f"{base_name}_data.xlsx"
        try:
            saved_files['data_excel'] = save_to_excel(df, str(excel_path))
        except ImportError:
            logger.warning("openpyxl not installed, skipping Excel export")
    
    # Save statistics
    if 'json' in formats:
        stats_path = output_dir / f"{base_name}_stats.json"
        saved_files['stats_json'] = save_to_json(stats, str(stats_path))
    
    # Also save a simple data JSON
    if 'json' in formats:
        data_json_path = output_dir / f"{base_name}_data.json"
        saved_files['data_json'] = save_to_json(df, str(data_json_path))
    
    logger.info(f"Saved {len(saved_files)} files to {output_dir}")
    
    return saved_files


def load_from_csv(input_path: str, encoding: str = 'utf-8-sig') -> pd.DataFrame:
    """
    Load DataFrame from CSV file.
    
    Args:
        input_path: Input file path
        encoding: File encoding
        
    Returns:
        pd.DataFrame: Loaded data
    """
    df = pd.read_csv(input_path, encoding=encoding)
    logger.info(f"Loaded {len(df)} rows from CSV: {input_path}")
    return df


def load_from_json(input_path: str) -> Any:
    """
    Load data from JSON file.
    
    Args:
        input_path: Input file path
        
    Returns:
        Loaded data (dict or list)
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded data from JSON: {input_path}")
    return data


def create_sample_data(num_posts: int = 50) -> pd.DataFrame:
    """
    Create sample data for testing.
    
    Args:
        num_posts: Number of sample posts to create
        
    Returns:
        pd.DataFrame: Sample data
    """
    import random
    from datetime import timedelta
    
    sample_texts = [
        "İklim değişikliği konusunda acil önlem almamız gerekiyor.",
        "Yenilenebilir enerji kaynaklarına yatırım artmalı.",
        "Karbon emisyonlarını azaltmak için herkes sorumluluk almalı.",
        "Bu konu hakkında daha fazla bilinçlendirme yapılmalı.",
        "Çevre kirliliği geleceğimizi tehdit ediyor.",
        "Sürdürülebilir yaşam için atık yönetimi önemli.",
        "Elektrikli araçlar daha yaygınlaşmalı.",
        "Orman yangınları iklim krizinin bir sonucu.",
        "Su kaynaklarımızı korumak için harekete geçmeliyiz.",
        "Sera gazı emisyonları endişe verici boyutlara ulaştı.",
    ]
    
    sample_authors = [
        "user1", "user2", "user3", "user4", "user5",
        "climate_activist", "eco_warrior", "green_future",
        "nature_lover", "earth_protector"
    ]
    
    base_date = datetime.now()
    
    data = []
    for i in range(num_posts):
        post = {
            'id': str(1000 + i),
            'text': random.choice(sample_texts),
            'author': random.choice(sample_authors),
            'created_at': (base_date - timedelta(days=random.randint(0, 30))).isoformat(),
            'reblogs_count': random.randint(0, 50),
            'favourites_count': random.randint(0, 100),
            'replies_count': random.randint(0, 20),
            'instance': 'https://mastodon.social',
        }
        data.append(post)
    
    df = pd.DataFrame(data)
    logger.info(f"Created {num_posts} sample posts")
    
    return df

