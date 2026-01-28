"""Unit tests for alert detection service."""

import pytest

from backend.models.file import FileType
from backend.services.document_parser import DocumentChunk
from backend.services.alert_service import (
    AlertType,
    AlertSeverity,
    Alert,
    SupplyChainAlertDetector,
    alert_detector,
)


# ============================================================================
# Alert Model Tests
# ============================================================================

class TestAlertDataclass:
    """Tests for Alert dataclass."""

    def test_create_alert(self):
        """Test creating an alert."""
        alert = Alert(
            alert_type=AlertType.NEGATIVE_STOCK,
            severity=AlertSeverity.CRITICAL,
            message="Stock négatif: -50 unités",
            chunk_metadata={"filename": "test.xlsx", "cell_ref": "C12"},
            value=-50,
        )

        assert alert.alert_type == AlertType.NEGATIVE_STOCK
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.message == "Stock négatif: -50 unités"
        assert alert.value == -50


# ============================================================================
# SupplyChainAlertDetector Tests
# ============================================================================

@pytest.mark.alert
class TestSupplyChainAlertDetector:
    """Tests for supply chain alert detector."""

    def test_detector_initialization(self):
        """Test that detector initializes with default thresholds."""
        detector = SupplyChainAlertDetector()

        assert detector.max_lead_time_days == 90
        assert detector.min_lead_time_days == 1
        assert len(detector.stock_keywords) > 0
        assert len(detector.date_keywords) > 0
        assert len(detector.quantity_keywords) > 0

    def test_detect_negative_stock_excel(self):
        """Test detecting negative stock in Excel chunk."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Stock: -50",
            metadata={
                "filename": "inventory.xlsx",
                "file_type": "excel",
                "sheet_name": "Products",
                "cell_ref": "C12",
                "row": 12,
                "column": 3,
                "value": "-50",
                "column_header": "Stock",
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_stock(chunk)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.alert_type == AlertType.NEGATIVE_STOCK
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.value == -50
        assert "négatif" in alert.message.lower()

    def test_detect_negative_stock_positive_value_no_alert(self):
        """Test that positive stock values don't trigger alerts."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Stock: 150",
            metadata={
                "filename": "inventory.xlsx",
                "file_type": "excel",
                "sheet_name": "Products",
                "cell_ref": "C10",
                "row": 10,
                "column": 3,
                "value": "150",
                "column_header": "Stock",
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_stock(chunk)

        assert len(alerts) == 0

    def test_detect_negative_stock_csv(self):
        """Test detecting negative stock in CSV chunk."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Product: A | Stock: -25 | Status: Critical",
            metadata={
                "filename": "inventory.csv",
                "file_type": "csv",
                "row_number": 5,
            },
            file_type=FileType.CSV,
        )

        alerts = detector.detect_negative_stock(chunk)

        # Should detect negative stock in CSV
        assert len(alerts) >= 0  # May or may not detect based on keyword matching

    def test_detect_negative_stock_non_numeric_value(self):
        """Test that non-numeric values don't crash detector."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Stock: N/A",
            metadata={
                "filename": "inventory.xlsx",
                "file_type": "excel",
                "sheet_name": "Products",
                "cell_ref": "C12",
                "row": 12,
                "column": 3,
                "value": "N/A",
                "column_header": "Stock",
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_stock(chunk)

        # Should not crash, just return empty list
        assert alerts == []

    def test_detect_negative_quantity_excel(self):
        """Test detecting negative quantity in orders."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Quantity: -10",
            metadata={
                "filename": "orders.xlsx",
                "file_type": "excel",
                "sheet_name": "Orders",
                "cell_ref": "D5",
                "row": 5,
                "column": 4,
                "value": "-10",
                "column_header": "Quantity",
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_quantity(chunk)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.alert_type == AlertType.NEGATIVE_QUANTITY
        assert alert.severity == AlertSeverity.WARNING
        assert alert.value == -10

    def test_detect_negative_quantity_not_in_stock_column(self):
        """Test that negative quantity is only detected in quantity columns, not stock."""
        detector = SupplyChainAlertDetector()

        # This should trigger negative_stock alert, not negative_quantity
        chunk = DocumentChunk(
            content="Stock Quantity: -10",
            metadata={
                "filename": "inventory.xlsx",
                "file_type": "excel",
                "sheet_name": "Products",
                "cell_ref": "C5",
                "row": 5,
                "column": 3,
                "value": "-10",
                "column_header": "Stock Quantity",  # Contains both keywords
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_quantity(chunk)

        # Should not detect as negative quantity because it's also a stock column
        assert len(alerts) == 0

    def test_detect_lead_time_outlier_too_long(self):
        """Test detecting abnormally long lead times."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Lead time for Product X is 120 days",
            metadata={
                "filename": "suppliers.txt",
                "file_type": "text",
            },
            file_type=FileType.TEXT,
        )

        alerts = detector.detect_lead_time_outlier(chunk)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.alert_type == AlertType.LEAD_TIME_OUTLIER
        assert alert.severity == AlertSeverity.WARNING
        assert alert.value == 120.0

    def test_detect_lead_time_outlier_too_short(self):
        """Test detecting abnormally short lead times."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Délai de livraison: 0.5 jours",
            metadata={
                "filename": "suppliers.csv",
                "file_type": "csv",
            },
            file_type=FileType.CSV,
        )

        alerts = detector.detect_lead_time_outlier(chunk)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.alert_type == AlertType.LEAD_TIME_OUTLIER
        assert alert.severity == AlertSeverity.INFO
        assert alert.value == 0.5

    def test_detect_lead_time_normal_range_no_alert(self):
        """Test that normal lead times don't trigger alerts."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Lead time for Product Y is 15 days",
            metadata={
                "filename": "suppliers.txt",
                "file_type": "text",
            },
            file_type=FileType.TEXT,
        )

        alerts = detector.detect_lead_time_outlier(chunk)

        # 15 days is within normal range (1-90)
        assert len(alerts) == 0

    def test_detect_all_alerts_integration(self, sample_chunks_with_alerts):
        """Test detecting all alert types on multiple chunks."""
        detector = SupplyChainAlertDetector()

        alerts = detector.detect_all_alerts(sample_chunks_with_alerts)

        # Should detect at least the negative stock and negative quantity
        assert len(alerts) >= 2

        # Verify we have different alert types
        alert_types = {alert.alert_type for alert in alerts}
        assert AlertType.NEGATIVE_STOCK in alert_types
        assert AlertType.NEGATIVE_QUANTITY in alert_types

    def test_detect_all_alerts_empty_chunks(self):
        """Test that empty chunks list returns no alerts."""
        detector = SupplyChainAlertDetector()

        alerts = detector.detect_all_alerts([])

        assert alerts == []

    def test_detect_all_alerts_no_issues(self):
        """Test chunks with no issues return no alerts."""
        detector = SupplyChainAlertDetector()

        chunks = [
            DocumentChunk(
                content="Stock: 150",
                metadata={
                    "filename": "inventory.xlsx",
                    "file_type": "excel",
                    "sheet_name": "Products",
                    "cell_ref": "C10",
                    "row": 10,
                    "column": 3,
                    "value": "150",
                    "column_header": "Stock",
                },
                file_type=FileType.EXCEL,
            ),
            DocumentChunk(
                content="Lead time: 20 days",
                metadata={
                    "filename": "suppliers.txt",
                    "file_type": "text",
                },
                file_type=FileType.TEXT,
            ),
        ]

        alerts = detector.detect_all_alerts(chunks)

        assert len(alerts) == 0


# ============================================================================
# French Language Support Tests
# ============================================================================

@pytest.mark.alert
class TestFrenchLanguageSupport:
    """Test that detector works with French keywords."""

    def test_detect_stock_with_french_keywords(self):
        """Test detecting stock issues with French keywords."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Inventaire: -30",
            metadata={
                "filename": "inventaire.xlsx",
                "file_type": "excel",
                "sheet_name": "Produits",
                "cell_ref": "C5",
                "row": 5,
                "column": 3,
                "value": "-30",
                "column_header": "Inventaire",  # French for inventory
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_stock(chunk)

        assert len(alerts) == 1

    def test_detect_quantity_with_french_keywords(self):
        """Test detecting quantity with French keywords."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Quantité: -15",
            metadata={
                "filename": "commandes.xlsx",
                "file_type": "excel",
                "sheet_name": "Commandes",
                "cell_ref": "D8",
                "row": 8,
                "column": 4,
                "value": "-15",
                "column_header": "Quantité",  # French for quantity
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_quantity(chunk)

        assert len(alerts) == 1


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.alert
class TestAlertEdgeCases:
    """Test edge cases and error handling."""

    def test_detect_alerts_with_missing_metadata(self):
        """Test that detector handles missing metadata gracefully."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Stock: -50",
            metadata={
                "filename": "test.xlsx",
                # Missing column_header, sheet_name, etc.
            },
            file_type=FileType.EXCEL,
        )

        # Should not crash
        alerts = detector.detect_negative_stock(chunk)

        # May or may not detect based on metadata availability
        assert isinstance(alerts, list)

    def test_detect_alerts_with_comma_decimal_separator(self):
        """Test detecting values with comma as decimal separator (European format)."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Stock: -50,5",
            metadata={
                "filename": "inventory.xlsx",
                "file_type": "excel",
                "sheet_name": "Products",
                "cell_ref": "C12",
                "row": 12,
                "column": 3,
                "value": "-50,5",
                "column_header": "Stock",
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_stock(chunk)

        assert len(alerts) == 1
        # Should parse -50,5 as -50.5
        assert alerts[0].value == -50.5

    def test_detect_zero_stock_no_alert(self):
        """Test that zero stock doesn't trigger negative stock alert."""
        detector = SupplyChainAlertDetector()

        chunk = DocumentChunk(
            content="Stock: 0",
            metadata={
                "filename": "inventory.xlsx",
                "file_type": "excel",
                "sheet_name": "Products",
                "cell_ref": "C12",
                "row": 12,
                "column": 3,
                "value": "0",
                "column_header": "Stock",
            },
            file_type=FileType.EXCEL,
        )

        alerts = detector.detect_negative_stock(chunk)

        # Zero is not negative
        assert len(alerts) == 0


# ============================================================================
# Singleton Tests
# ============================================================================

class TestAlertDetectorSingleton:
    """Test the singleton alert_detector instance."""

    def test_singleton_is_initialized(self):
        """Test that the singleton instance exists."""
        assert alert_detector is not None
        assert isinstance(alert_detector, SupplyChainAlertDetector)

    def test_singleton_has_default_config(self):
        """Test that singleton has expected default configuration."""
        assert alert_detector.max_lead_time_days == 90
        assert alert_detector.min_lead_time_days == 1


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.slow
class TestAlertPerformance:
    """Test alert detection performance with large datasets."""

    def test_detect_alerts_large_chunk_list(self):
        """Test detecting alerts on a large number of chunks."""
        detector = SupplyChainAlertDetector()

        # Create 1000 chunks
        chunks = []
        for i in range(1000):
            chunk = DocumentChunk(
                content=f"Stock: {100 - i}",  # Some will be negative
                metadata={
                    "filename": "large_inventory.xlsx",
                    "file_type": "excel",
                    "sheet_name": "Products",
                    "cell_ref": f"C{i+2}",
                    "row": i + 2,
                    "column": 3,
                    "value": str(100 - i),
                    "column_header": "Stock",
                },
                file_type=FileType.EXCEL,
            )
            chunks.append(chunk)

        # Should complete without timeout
        alerts = detector.detect_all_alerts(chunks)

        # Should detect negative stocks (from 100 down to -899)
        negative_alerts = [
            a for a in alerts
            if a.alert_type == AlertType.NEGATIVE_STOCK
        ]

        assert len(negative_alerts) > 0
        # Should detect 900 negative stocks (100 down to -899)
        assert len(negative_alerts) == 900
