"""Temporal analysis service for detecting and analyzing time-based patterns in Supply Chain data."""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
import pandas as pd
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


# Patterns for detecting temporal columns (case-insensitive)
DATE_COLUMN_PATTERNS = [
    r'date',
    r'delivery.*date', r'livraison', r'reception',
    r'order.*date', r'commande',
    r'ship.*date', r'expedition', r'envoi',
    r'due.*date', r'echeance',
    r'timestamp', r'datetime',
]

# Blacklist patterns to ignore (system columns)
BLACKLIST_PATTERNS = [
    r'created_at', r'updated_at', r'deleted_at', r'last_modified',
    r'created_by', r'updated_by', r'deleted_by',
]


class TemporalService:
    """Service for temporal analysis: detection, lead time calculation, and trend analysis."""

    def __init__(self):
        """Initialize temporal service."""
        self.date_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in DATE_COLUMN_PATTERNS]
        self.blacklist_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in BLACKLIST_PATTERNS]

    def detect_temporal_columns(
        self,
        df: pd.DataFrame,
        column_names: List[str],
        min_valid_ratio: float = 0.1,
    ) -> List[str]:
        """
        Detect temporal columns in a DataFrame using name patterns and format validation.

        Args:
            df: DataFrame to analyze
            column_names: List of column names to check
            min_valid_ratio: Minimum ratio of valid dates required (default: 10%)

        Returns:
            List of column names that are temporal
        """
        temporal_cols = []

        for col in column_names:
            # Skip blacklisted columns
            if any(pattern.search(col) for pattern in self.blacklist_patterns):
                logger.debug(f"Skipping blacklisted column: {col}")
                continue

            # Check if column name matches temporal patterns
            if not any(pattern.search(col) for pattern in self.date_patterns):
                continue

            # Validate column content (check if it contains dates)
            if col not in df.columns:
                continue

            # Check if column has datetime dtype
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                temporal_cols.append(col)
                logger.info(f"Detected temporal column (datetime dtype): {col}")
                continue

            # For non-datetime columns, try parsing as dates
            non_null_values = df[col].dropna()
            if len(non_null_values) == 0:
                continue

            # Check data sparsity: reject columns with <10% non-null values
            sparsity_ratio = len(non_null_values) / len(df)
            if sparsity_ratio < 0.10:
                logger.debug(f"Skipping sparse column {col}: only {sparsity_ratio:.1%} non-null values")
                continue

            # Sample up to 100 rows for validation
            sample_size = min(100, len(non_null_values))
            sample = non_null_values.sample(n=sample_size, random_state=42)

            valid_dates = 0
            for value in sample:
                if self._is_valid_date(value):
                    valid_dates += 1

            valid_ratio = valid_dates / sample_size

            if valid_ratio >= min_valid_ratio:
                temporal_cols.append(col)
                logger.info(f"Detected temporal column (format validation: {valid_ratio:.1%}): {col}")

        return temporal_cols

    def _is_valid_date(self, value: Any) -> bool:
        """
        Check if a value is a valid date.

        Args:
            value: Value to check

        Returns:
            True if value is a valid date
        """
        if pd.isna(value):
            return False

        try:
            # Try parsing with dateutil (handles many formats)
            date_parser.parse(str(value))
            return True
        except (ValueError, TypeError, OverflowError):
            return False

    def calculate_lead_times(
        self,
        df: pd.DataFrame,
        start_col: str,
        end_col: str,
    ) -> Dict[str, Any]:
        """
        Calculate lead times (delays) between two date columns.

        Args:
            df: DataFrame with temporal columns
            start_col: Start date column name
            end_col: End date column name

        Returns:
            Dictionary with lead time statistics
        """
        try:
            # Convert columns to datetime if needed
            start_dates = pd.to_datetime(df[start_col], errors='coerce')
            end_dates = pd.to_datetime(df[end_col], errors='coerce')

            # Calculate lead times in days
            lead_times = (end_dates - start_dates).dt.days

            # Filter out invalid lead times (NaN or negative)
            valid_lead_times = lead_times.dropna()
            valid_lead_times = valid_lead_times[valid_lead_times >= 0]

            if len(valid_lead_times) == 0:
                logger.warning(f"No valid lead times found between {start_col} and {end_col}")
                return {}

            # Calculate statistics
            mean_days = float(valid_lead_times.mean())
            median_days = float(valid_lead_times.median())
            max_days = float(valid_lead_times.max())
            min_days = float(valid_lead_times.min())
            std_days = float(valid_lead_times.std())

            # Detect outliers (>2 std dev from mean)
            outlier_threshold = mean_days + 2 * std_days
            outliers = valid_lead_times[valid_lead_times > outlier_threshold].tolist()

            stats = {
                'mean_days': round(mean_days, 2),
                'median_days': round(median_days, 2),
                'max_days': round(max_days, 2),
                'min_days': round(min_days, 2),
                'std_days': round(std_days, 2),
                'outliers': [round(x, 2) for x in outliers[:10]],  # Max 10 outliers
                'total_records': len(valid_lead_times),
            }

            logger.info(f"Lead time stats: mean={mean_days:.1f}d, median={median_days:.1f}d, outliers={len(outliers)}")
            return stats

        except Exception as e:
            logger.error(f"Error calculating lead times: {e}", exc_info=True)
            return {}

    def extract_time_range(
        self,
        df: pd.DataFrame,
        temporal_cols: List[str],
    ) -> Optional[Dict[str, str]]:
        """
        Extract the earliest and latest dates from temporal columns.

        Args:
            df: DataFrame with temporal columns
            temporal_cols: List of temporal column names

        Returns:
            Dictionary with earliest and latest dates (ISO format)
        """
        if not temporal_cols:
            return None

        try:
            all_dates = []

            for col in temporal_cols:
                dates = pd.to_datetime(df[col], errors='coerce').dropna()
                all_dates.extend(dates.tolist())

            if not all_dates:
                return None

            earliest = min(all_dates)
            latest = max(all_dates)

            return {
                'earliest': earliest.strftime('%Y-%m-%d'),
                'latest': latest.strftime('%Y-%m-%d'),
            }

        except Exception as e:
            logger.error(f"Error extracting time range: {e}", exc_info=True)
            return None

    def calculate_trends(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        min_months_for_seasonality: int = 6,
    ) -> Dict[str, Any]:
        """
        Calculate trends and seasonality for time series data.

        Args:
            df: DataFrame with temporal and value columns
            date_col: Date column name
            value_col: Value column name (numeric)
            min_months_for_seasonality: Minimum months of data for seasonality detection

        Returns:
            Dictionary with trend metrics
        """
        try:
            # Convert to datetime and sort
            df_sorted = df.copy()
            df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors='coerce')
            df_sorted = df_sorted.dropna(subset=[date_col, value_col])
            df_sorted = df_sorted.sort_values(date_col)

            if len(df_sorted) < 2:
                logger.warning("Insufficient data for trend analysis (need at least 2 points)")
                return {}

            # Calculate rolling averages
            rolling_7d = df_sorted[value_col].rolling(window=min(7, len(df_sorted)), min_periods=1).mean()
            rolling_30d = df_sorted[value_col].rolling(window=min(30, len(df_sorted)), min_periods=1).mean()

            trends = {
                'rolling_avg_7d': rolling_7d.tolist(),
                'rolling_avg_30d': rolling_30d.tolist(),
            }

            # Calculate monthly variation if data spans multiple months
            df_sorted['year_month'] = df_sorted[date_col].dt.to_period('M')
            monthly_avg = df_sorted.groupby('year_month')[value_col].mean()

            if len(monthly_avg) >= 2:
                # Calculate month-over-month variation
                monthly_variation = monthly_avg.pct_change() * 100
                trends['monthly_variation_pct'] = monthly_variation.dropna().tolist()

            # Detect seasonality if data spans >= min_months_for_seasonality
            time_span = (df_sorted[date_col].max() - df_sorted[date_col].min()).days / 30
            if time_span >= min_months_for_seasonality:
                seasonality = self._detect_seasonality(df_sorted, date_col, value_col)
                if seasonality:
                    trends['seasonality'] = seasonality

            logger.info(f"Calculated trends for {len(df_sorted)} data points")
            return trends

        except Exception as e:
            logger.error(f"Error calculating trends: {e}", exc_info=True)
            return {}

    def _detect_seasonality(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Detect seasonal patterns in time series data.

        Args:
            df: Sorted DataFrame with date and value columns
            date_col: Date column name
            value_col: Value column name

        Returns:
            Dictionary with seasonality info or None
        """
        try:
            # Calculate average by month
            df['month'] = df[date_col].dt.month
            monthly_avg = df.groupby('month')[value_col].mean()

            if len(monthly_avg) < 6:
                return None

            # Find peak and low months
            peak_month = monthly_avg.idxmax()
            low_month = monthly_avg.idxmin()
            overall_avg = monthly_avg.mean()

            # Calculate peak/low deviation from average
            peak_deviation = ((monthly_avg[peak_month] - overall_avg) / overall_avg) * 100
            low_deviation = ((monthly_avg[low_month] - overall_avg) / overall_avg) * 100

            # Only consider significant seasonality (>15% deviation)
            if abs(peak_deviation) < 15:
                return None

            month_names_fr = [
                'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
            ]

            pattern_desc = f"Pic en {month_names_fr[peak_month - 1]} ({peak_deviation:+.1f}%)"
            if abs(low_deviation) > 15:
                pattern_desc += f", creux en {month_names_fr[low_month - 1]} ({low_deviation:+.1f}%)"

            return {
                'peak_month': int(peak_month),
                'peak_month_name': month_names_fr[peak_month - 1],
                'peak_deviation_pct': round(peak_deviation, 1),
                'low_month': int(low_month),
                'low_month_name': month_names_fr[low_month - 1],
                'low_deviation_pct': round(low_deviation, 1),
                'pattern_description': pattern_desc,
            }

        except Exception as e:
            logger.error(f"Error detecting seasonality: {e}", exc_info=True)
            return None

    def identify_lead_time_pairs(
        self,
        temporal_cols: List[str],
    ) -> List[Tuple[str, str]]:
        """
        Identify likely pairs of (start_date, end_date) columns for lead time calculation.

        Args:
            temporal_cols: List of detected temporal column names

        Returns:
            List of (start_col, end_col) tuples
        """
        if len(temporal_cols) == 2:
            # If exactly 2 columns, assume (start, end) pair
            return [(temporal_cols[0], temporal_cols[1])]

        if len(temporal_cols) < 2:
            return []

        # Try to match common patterns
        pairs = []

        # Pattern matching for common column name combinations
        start_patterns = [
            (r'order.*date', r'delivery.*date'),
            (r'commande', r'livraison'),
            (r'ship.*date', r'receive.*date'),
            (r'expedition', r'reception'),
            (r'start', r'end'),
            (r'debut', r'fin'),
        ]

        for start_pattern, end_pattern in start_patterns:
            start_re = re.compile(start_pattern, re.IGNORECASE)
            end_re = re.compile(end_pattern, re.IGNORECASE)

            start_cols = [col for col in temporal_cols if start_re.search(col)]
            end_cols = [col for col in temporal_cols if end_re.search(col)]

            if start_cols and end_cols:
                pairs.append((start_cols[0], end_cols[0]))

        # If no pattern matches found, return empty (user config needed)
        if not pairs:
            logger.info(f"Could not auto-identify lead time pairs from {len(temporal_cols)} columns")

        return pairs


# Singleton instance
temporal_service = TemporalService()
