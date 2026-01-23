"""Alert detection service for Supply Chain anomalies."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from backend.services.document_parser import DocumentChunk


logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types of supply chain alerts."""
    NEGATIVE_STOCK = "negative_stock"
    DATE_INCONSISTENCY = "date_inconsistency"
    NEGATIVE_QUANTITY = "negative_quantity"
    LEAD_TIME_OUTLIER = "lead_time_outlier"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Alert:
    """Alert detection result."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    chunk_metadata: Dict[str, Any]
    value: Optional[Any] = None


class SupplyChainAlertDetector:
    """Detector for Supply Chain anomalies and inconsistencies."""

    def __init__(self):
        """Initialize alert detector with configurable thresholds."""
        # Configurable thresholds
        self.max_lead_time_days = 90
        self.min_lead_time_days = 1

        # Column keywords for detection
        self.stock_keywords = ['stock', 'inventory', 'quantity', 'qty', 'quantité', 'inventaire']
        self.date_keywords = ['date', 'livraison', 'delivery', 'commande', 'order']
        self.quantity_keywords = ['quantity', 'qty', 'quantité', 'qté']

    def detect_all_alerts(self, chunks: List[DocumentChunk]) -> List[Alert]:
        """
        Detect all types of alerts in document chunks.

        Args:
            chunks: Parsed document chunks

        Returns:
            List of detected alerts
        """
        alerts = []

        for chunk in chunks:
            # Detect negative stocks
            alerts.extend(self.detect_negative_stock(chunk))

            # Detect negative quantities
            alerts.extend(self.detect_negative_quantity(chunk))

            # Detect date inconsistencies (only for structured data)
            if chunk.file_type.value in ['excel', 'csv']:
                alerts.extend(self.detect_date_inconsistency(chunk))

            # Detect lead time outliers (only for structured data)
            if chunk.file_type.value in ['excel', 'csv']:
                alerts.extend(self.detect_lead_time_outlier(chunk))

        logger.info(f"Detected {len(alerts)} alerts across {len(chunks)} chunks")
        return alerts

    def detect_negative_stock(self, chunk: DocumentChunk) -> List[Alert]:
        """
        Detect negative stock values.

        Args:
            chunk: Document chunk to analyze

        Returns:
            List of alerts for negative stocks
        """
        alerts = []

        try:
            # Check if chunk is related to stock/inventory
            content_lower = chunk.content.lower()
            metadata = chunk.metadata

            # For Excel cells with column headers
            if chunk.file_type.value == 'excel':
                column_header = metadata.get('column_header', '').lower()
                value_str = metadata.get('value', '')

                # Check if column is stock-related
                if any(keyword in column_header for keyword in self.stock_keywords):
                    # Try to parse value as number
                    try:
                        value = float(str(value_str).replace(',', '.'))
                        if value < 0:
                            alert = Alert(
                                alert_type=AlertType.NEGATIVE_STOCK,
                                severity=AlertSeverity.CRITICAL,
                                message=f"Stock négatif détecté: {value} unités",
                                chunk_metadata=metadata,
                                value=value,
                            )
                            alerts.append(alert)
                            logger.warning(f"Negative stock detected: {value} in {metadata.get('cell_ref')}")
                    except (ValueError, TypeError):
                        pass

            # For CSV with column headers
            elif chunk.file_type.value == 'csv':
                # Parse content for negative values in stock columns
                for keyword in self.stock_keywords:
                    if keyword in content_lower:
                        # Extract numeric values
                        numbers = re.findall(r'-?\d+\.?\d*', chunk.content)
                        for num_str in numbers:
                            try:
                                value = float(num_str)
                                if value < 0:
                                    alert = Alert(
                                        alert_type=AlertType.NEGATIVE_STOCK,
                                        severity=AlertSeverity.CRITICAL,
                                        message=f"Stock négatif détecté: {value} unités",
                                        chunk_metadata=metadata,
                                        value=value,
                                    )
                                    alerts.append(alert)
                            except (ValueError, TypeError):
                                pass

        except Exception as e:
            logger.error(f"Error detecting negative stock: {e}")

        return alerts

    def detect_negative_quantity(self, chunk: DocumentChunk) -> List[Alert]:
        """
        Detect negative quantity values in orders/deliveries.

        Args:
            chunk: Document chunk to analyze

        Returns:
            List of alerts for negative quantities
        """
        alerts = []

        try:
            content_lower = chunk.content.lower()
            metadata = chunk.metadata

            # For Excel cells
            if chunk.file_type.value == 'excel':
                column_header = metadata.get('column_header', '').lower()
                value_str = metadata.get('value', '')

                # Check if column is quantity-related (but not stock)
                is_quantity_col = any(keyword in column_header for keyword in self.quantity_keywords)
                is_stock_col = any(keyword in column_header for keyword in self.stock_keywords)

                if is_quantity_col and not is_stock_col:
                    try:
                        value = float(str(value_str).replace(',', '.'))
                        if value < 0:
                            alert = Alert(
                                alert_type=AlertType.NEGATIVE_QUANTITY,
                                severity=AlertSeverity.WARNING,
                                message=f"Quantité négative détectée: {value}",
                                chunk_metadata=metadata,
                                value=value,
                            )
                            alerts.append(alert)
                    except (ValueError, TypeError):
                        pass

        except Exception as e:
            logger.error(f"Error detecting negative quantity: {e}")

        return alerts

    def detect_date_inconsistency(self, chunk: DocumentChunk) -> List[Alert]:
        """
        Detect date inconsistencies (e.g., delivery before order).

        Args:
            chunk: Document chunk to analyze

        Returns:
            List of alerts for date inconsistencies
        """
        alerts = []

        try:
            # This is a simplified implementation
            # In production, you'd want to correlate across multiple chunks/rows
            # For now, we detect obvious date issues within the same chunk

            content = chunk.content.lower()
            metadata = chunk.metadata

            # Look for date-related content
            if any(keyword in content for keyword in self.date_keywords):
                # Extract dates (basic pattern matching)
                # This could be enhanced with dateutil.parser
                date_patterns = [
                    r'\d{1,2}/\d{1,2}/\d{2,4}',  # DD/MM/YYYY or MM/DD/YYYY
                    r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                ]

                dates_found = []
                for pattern in date_patterns:
                    matches = re.findall(pattern, chunk.content)
                    dates_found.extend(matches)

                # For now, just log if we find multiple dates
                # More sophisticated logic would parse and compare dates
                if len(dates_found) >= 2:
                    logger.debug(f"Multiple dates found in chunk: {dates_found}")
                    # TODO: Implement date parsing and comparison

        except Exception as e:
            logger.error(f"Error detecting date inconsistency: {e}")

        return alerts

    def detect_lead_time_outlier(self, chunk: DocumentChunk) -> List[Alert]:
        """
        Detect abnormally long or short lead times.

        Args:
            chunk: Document chunk to analyze

        Returns:
            List of alerts for lead time outliers
        """
        alerts = []

        try:
            content_lower = chunk.content.lower()
            metadata = chunk.metadata

            # Look for lead time mentions
            if 'lead time' in content_lower or 'délai' in content_lower:
                # Extract numeric values (days)
                numbers = re.findall(r'\d+\.?\d*', chunk.content)

                for num_str in numbers:
                    try:
                        days = float(num_str)

                        if days > self.max_lead_time_days:
                            alert = Alert(
                                alert_type=AlertType.LEAD_TIME_OUTLIER,
                                severity=AlertSeverity.WARNING,
                                message=f"Délai anormalement long: {days} jours (> {self.max_lead_time_days} jours)",
                                chunk_metadata=metadata,
                                value=days,
                            )
                            alerts.append(alert)

                        elif 0 < days < self.min_lead_time_days:
                            alert = Alert(
                                alert_type=AlertType.LEAD_TIME_OUTLIER,
                                severity=AlertSeverity.INFO,
                                message=f"Délai très court: {days} jours (< {self.min_lead_time_days} jour)",
                                chunk_metadata=metadata,
                                value=days,
                            )
                            alerts.append(alert)

                    except (ValueError, TypeError):
                        pass

        except Exception as e:
            logger.error(f"Error detecting lead time outlier: {e}")

        return alerts


# Singleton instance
alert_detector = SupplyChainAlertDetector()
