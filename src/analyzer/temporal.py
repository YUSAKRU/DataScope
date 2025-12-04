"""
Temporal analysis module for DataScope.

This module provides time-based analysis including
trend detection, peak analysis, and anomaly detection.
"""

from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TemporalAnalyzer:
    """
    Analyze temporal patterns in social media data.
    
    Provides:
    - Trend detection (increasing/decreasing)
    - Peak/valley detection
    - Periodic pattern analysis
    - Anomaly detection
    
    Example:
        >>> analyzer = TemporalAnalyzer()
        >>> results = analyzer.analyze(df, date_column='created_at')
        >>> print(results['trend'])
    """
    
    def __init__(self, min_periods: int = 3):
        """
        Initialize temporal analyzer.
        
        Args:
            min_periods: Minimum periods for analysis
        """
        self.min_periods = min_periods
    
    def analyze(self, df: pd.DataFrame, date_column: str = 'created_at') -> Dict[str, Any]:
        """
        Perform comprehensive temporal analysis.
        
        Args:
            df: DataFrame with date column
            date_column: Column containing timestamps
            
        Returns:
            Temporal analysis results
        """
        if date_column not in df.columns:
            return {'error': f"Column '{date_column}' not found"}
        
        # Convert to datetime
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column], format='ISO8601', errors='coerce')
        df = df.dropna(subset=[date_column])
        
        if len(df) < self.min_periods:
            return {'error': f"Not enough data points ({len(df)})"}
        
        results = {
            'date_range': self._get_date_range(df, date_column),
            'hourly_distribution': self._analyze_hourly(df, date_column),
            'daily_distribution': self._analyze_daily(df, date_column),
            'weekly_pattern': self._analyze_weekly(df, date_column),
            'trend': self._detect_trend(df, date_column),
            'peaks': self._detect_peaks(df, date_column),
            'activity_summary': self._get_activity_summary(df, date_column),
        }
        
        logger.info(f"Temporal analysis completed for {len(df)} records")
        
        return results
    
    def _get_date_range(self, df: pd.DataFrame, date_column: str) -> Dict:
        """Get date range information."""
        min_date = df[date_column].min()
        max_date = df[date_column].max()
        
        return {
            'start': min_date.isoformat() if pd.notna(min_date) else None,
            'end': max_date.isoformat() if pd.notna(max_date) else None,
            'duration_days': (max_date - min_date).days if pd.notna(min_date) and pd.notna(max_date) else 0,
            'total_records': len(df),
        }
    
    def _analyze_hourly(self, df: pd.DataFrame, date_column: str) -> Dict:
        """Analyze hourly distribution."""
        hours = df[date_column].dt.hour
        hourly_counts = hours.value_counts().sort_index()
        
        peak_hour = hourly_counts.idxmax()
        quiet_hour = hourly_counts.idxmin()
        
        return {
            'distribution': hourly_counts.to_dict(),
            'peak_hour': int(peak_hour),
            'peak_hour_label': f"{peak_hour:02d}:00 - {(peak_hour+1)%24:02d}:00",
            'quiet_hour': int(quiet_hour),
            'quiet_hour_label': f"{quiet_hour:02d}:00 - {(quiet_hour+1)%24:02d}:00",
        }
    
    def _analyze_daily(self, df: pd.DataFrame, date_column: str) -> Dict:
        """Analyze daily distribution."""
        dates = df[date_column].dt.date
        daily_counts = dates.value_counts().sort_index()
        
        if len(daily_counts) == 0:
            return {'distribution': {}, 'avg_posts_per_day': 0}
        
        return {
            'distribution': {str(k): int(v) for k, v in daily_counts.items()},
            'avg_posts_per_day': round(daily_counts.mean(), 2),
            'max_posts_day': str(daily_counts.idxmax()),
            'max_posts_count': int(daily_counts.max()),
            'min_posts_day': str(daily_counts.idxmin()),
            'min_posts_count': int(daily_counts.min()),
            'std_dev': round(daily_counts.std(), 2) if len(daily_counts) > 1 else 0,
        }
    
    def _analyze_weekly(self, df: pd.DataFrame, date_column: str) -> Dict:
        """Analyze weekly pattern."""
        day_names_tr = {
            0: 'Pazartesi',
            1: 'Salı',
            2: 'Çarşamba',
            3: 'Perşembe',
            4: 'Cuma',
            5: 'Cumartesi',
            6: 'Pazar'
        }
        
        days = df[date_column].dt.dayofweek
        day_counts = days.value_counts().sort_index()
        
        # Normalize to percentages
        total = day_counts.sum()
        day_percentages = {day_names_tr[k]: round(v / total * 100, 1) 
                          for k, v in day_counts.items()}
        
        peak_day = days.mode().iloc[0] if len(days.mode()) > 0 else 0
        
        return {
            'distribution': day_percentages,
            'counts': {day_names_tr.get(k, str(k)): int(v) for k, v in day_counts.items()},
            'most_active_day': day_names_tr.get(peak_day, 'Bilinmiyor'),
            'weekday_vs_weekend': {
                'weekday': int(day_counts[day_counts.index < 5].sum()) if any(day_counts.index < 5) else 0,
                'weekend': int(day_counts[day_counts.index >= 5].sum()) if any(day_counts.index >= 5) else 0,
            }
        }
    
    def _detect_trend(self, df: pd.DataFrame, date_column: str) -> Dict:
        """Detect overall trend (increasing/decreasing/stable)."""
        dates = df[date_column].dt.date
        daily_counts = dates.value_counts().sort_index()
        
        if len(daily_counts) < 3:
            return {'direction': 'insufficient_data', 'strength': 0}
        
        # Use linear regression for trend
        x = np.arange(len(daily_counts))
        y = daily_counts.values
        
        # Calculate slope using numpy polyfit
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction
        if slope > 0.5:
            direction = 'increasing'
            direction_tr = 'Artış Eğilimi 📈'
        elif slope < -0.5:
            direction = 'decreasing'
            direction_tr = 'Azalış Eğilimi 📉'
        else:
            direction = 'stable'
            direction_tr = 'Stabil ➡️'
        
        return {
            'direction': direction,
            'direction_label': direction_tr,
            'slope': round(slope, 4),
            'strength': round(abs(r_squared), 4),
            'interpretation': f"Günlük ortalama {abs(slope):.2f} post {'artış' if slope > 0 else 'azalış'}",
        }
    
    def _detect_peaks(self, df: pd.DataFrame, date_column: str) -> Dict:
        """Detect peak activity periods."""
        dates = df[date_column].dt.date
        daily_counts = dates.value_counts().sort_index()
        
        if len(daily_counts) < 3:
            return {'peaks': [], 'valleys': []}
        
        values = daily_counts.values
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        # Define threshold for peaks (2 standard deviations above mean)
        peak_threshold = mean_val + 1.5 * std_val
        valley_threshold = mean_val - 1.5 * std_val
        
        peaks = []
        valleys = []
        
        for date, count in daily_counts.items():
            if count >= peak_threshold:
                peaks.append({
                    'date': str(date),
                    'count': int(count),
                    'deviation': round((count - mean_val) / std_val, 2) if std_val > 0 else 0,
                })
            elif count <= valley_threshold and count > 0:
                valleys.append({
                    'date': str(date),
                    'count': int(count),
                    'deviation': round((mean_val - count) / std_val, 2) if std_val > 0 else 0,
                })
        
        return {
            'peaks': sorted(peaks, key=lambda x: x['count'], reverse=True)[:5],
            'valleys': sorted(valleys, key=lambda x: x['count'])[:5],
            'threshold_info': {
                'mean': round(mean_val, 2),
                'std': round(std_val, 2),
                'peak_threshold': round(peak_threshold, 2),
            }
        }
    
    def _get_activity_summary(self, df: pd.DataFrame, date_column: str) -> Dict:
        """Generate activity summary."""
        dates = df[date_column]
        
        # Time of day categories
        hour = dates.dt.hour
        morning = ((hour >= 6) & (hour < 12)).sum()
        afternoon = ((hour >= 12) & (hour < 18)).sum()
        evening = ((hour >= 18) & (hour < 24)).sum()
        night = ((hour >= 0) & (hour < 6)).sum()
        
        total = len(df)
        
        return {
            'time_of_day': {
                'Sabah (06-12)': {'count': int(morning), 'percentage': round(morning/total*100, 1)},
                'Öğleden Sonra (12-18)': {'count': int(afternoon), 'percentage': round(afternoon/total*100, 1)},
                'Akşam (18-24)': {'count': int(evening), 'percentage': round(evening/total*100, 1)},
                'Gece (00-06)': {'count': int(night), 'percentage': round(night/total*100, 1)},
            },
            'most_active_period': max(
                [('Sabah', morning), ('Öğleden Sonra', afternoon), 
                 ('Akşam', evening), ('Gece', night)],
                key=lambda x: x[1]
            )[0]
        }


def analyze_temporal(df: pd.DataFrame, date_column: str = 'created_at') -> Dict:
    """
    Convenience function for temporal analysis.
    
    Args:
        df: DataFrame with date column
        date_column: Name of date column
        
    Returns:
        Temporal analysis results
    """
    analyzer = TemporalAnalyzer()
    return analyzer.analyze(df, date_column)


def get_temporal_summary(results: Dict) -> str:
    """Generate text summary of temporal analysis."""
    lines = ["⏰ Zaman Analizi Özeti", "=" * 40]
    
    # Date range
    date_range = results.get('date_range', {})
    lines.append(f"\n📅 Tarih Aralığı:")
    lines.append(f"  • Başlangıç: {date_range.get('start', 'N/A')[:10]}")
    lines.append(f"  • Bitiş: {date_range.get('end', 'N/A')[:10]}")
    lines.append(f"  • Süre: {date_range.get('duration_days', 0)} gün")
    
    # Trend
    trend = results.get('trend', {})
    lines.append(f"\n📊 Trend: {trend.get('direction_label', 'N/A')}")
    lines.append(f"  • {trend.get('interpretation', '')}")
    
    # Peak activity
    hourly = results.get('hourly_distribution', {})
    lines.append(f"\n🕐 En Aktif Saat: {hourly.get('peak_hour_label', 'N/A')}")
    
    weekly = results.get('weekly_pattern', {})
    lines.append(f"📆 En Aktif Gün: {weekly.get('most_active_day', 'N/A')}")
    
    # Activity periods
    activity = results.get('activity_summary', {})
    lines.append(f"🌅 En Yoğun Zaman Dilimi: {activity.get('most_active_period', 'N/A')}")
    
    # Peaks
    peaks = results.get('peaks', {}).get('peaks', [])
    if peaks:
        lines.append(f"\n🔥 Yoğunluk Zirveleri:")
        for peak in peaks[:3]:
            lines.append(f"  • {peak['date']}: {peak['count']} gönderi")
    
    return "\n".join(lines)


