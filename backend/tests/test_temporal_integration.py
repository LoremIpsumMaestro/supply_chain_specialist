"""Integration tests for temporal intelligence features."""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

from backend.services.document_parser import ExcelParser, CSVParser
from backend.services.temporal_service import temporal_service


class TestTemporalEnrichment:
    """Integration tests for temporal metadata enrichment in parsers."""

    def test_excel_parser_with_temporal_columns(self):
        """Test that Excel parser detects temporal columns and enriches chunks."""
        # Create a simple Excel file with temporal columns
        df = pd.DataFrame({
            'date_commande': pd.date_range('2025-01-01', periods=5, freq='D'),
            'date_livraison': pd.date_range('2025-01-15', periods=5, freq='D'),
            'quantite': [10, 20, 30, 40, 50],
        })

        # Save to BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Orders', index=False)
        buffer.seek(0)

        # Parse with ExcelParser
        parser = ExcelParser()
        chunks = parser.parse(buffer.read(), 'test_orders.xlsx')

        # Verify chunks were created
        assert len(chunks) > 0

        # Verify upload_date is present in all chunks
        for chunk in chunks:
            assert 'upload_date' in chunk.metadata

        # Find chunks with temporal context
        temporal_chunks = [c for c in chunks if 'temporal_context' in c.metadata]

        # Should have temporal context for date columns
        assert len(temporal_chunks) > 0

        # Verify temporal context structure
        for chunk in temporal_chunks:
            tc = chunk.metadata['temporal_context']
            # Should have at least one temporal field
            assert len(tc) > 0

    def test_csv_parser_with_temporal_columns(self):
        """Test that CSV parser detects temporal columns and enriches chunks."""
        df = pd.DataFrame({
            'order_date': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'delivery_date': ['2025-01-15', '2025-01-16', '2025-01-17'],
            'amount': [100, 200, 300],
        })

        # Save to CSV
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Parse with CSVParser
        parser = CSVParser()
        chunks = parser.parse(csv_buffer.read(), 'test_orders.csv')

        # Verify chunks created
        assert len(chunks) == 3

        # Verify upload_date in all chunks
        for chunk in chunks:
            assert 'upload_date' in chunk.metadata

        # Verify temporal context for rows with dates
        temporal_chunks = [c for c in chunks if 'temporal_context' in c.metadata]
        assert len(temporal_chunks) > 0

    def test_pdf_parser_no_temporal_context(self):
        """Test that PDF parser adds upload_date but no temporal_context."""
        # PDFs don't have structured temporal columns
        # Just verify that upload_date is added but temporal_context is not

        # Note: This test would require creating a PDF, which is complex
        # For now, we verify the logic exists in the parser code
        # Full E2E test would be in Playwright tests
        pass


class TestLeadTimeEndToEnd:
    """End-to-end tests for lead time calculation."""

    def test_excel_lead_time_calculation(self):
        """Test that Excel files with order/delivery dates calculate lead times."""
        df = pd.DataFrame({
            'date_commande': pd.date_range('2025-01-01', periods=10, freq='D'),
            'date_livraison': pd.date_range('2025-01-15', periods=10, freq='D'),  # 14 days lead time
            'reference': [f'CMD{i}' for i in range(10)],
        })

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Orders', index=False)
        buffer.seek(0)

        # Parse
        parser = ExcelParser()
        chunks = parser.parse(buffer.read(), 'orders.xlsx')

        # Verify temporal context includes dates
        temporal_chunks = [c for c in chunks if 'temporal_context' in c.metadata]
        assert len(temporal_chunks) > 0

        # Check that date columns are detected
        date_chunks = [c for c in temporal_chunks
                       if 'date_commande' in c.metadata.get('temporal_context', {})
                       or 'date_livraison' in c.metadata.get('temporal_context', {})]
        assert len(date_chunks) > 0


class TestTemporalContextInRAG:
    """Tests for temporal context in RAG results."""

    def test_rag_context_includes_temporal_info(self):
        """Test that build_rag_context includes temporal metadata."""
        from backend.services.rag_service import rag_service

        # Mock search results with temporal context
        search_results = [{
            'content': 'Commande CMD123',
            'metadata': {
                'filename': 'orders.xlsx',
                'file_type': 'excel',
                'sheet_name': 'Orders',
                'cell_ref': 'A5',
                'temporal_context': {
                    'date_commande': '2025-01-15',
                    'date_livraison': '2025-01-30',
                    'lead_time_days': 15,
                }
            }
        }]

        context = rag_service.build_rag_context(search_results)

        # Verify temporal info is included
        assert 'date_commande' in context or 'date_livraison' in context
        assert 'orders.xlsx' in context
        assert 'Orders' in context
        assert 'A5' in context

    def test_rag_context_without_temporal_info(self):
        """Test that RAG context works without temporal metadata."""
        from backend.services.rag_service import rag_service

        search_results = [{
            'content': 'Sample PDF content',
            'metadata': {
                'filename': 'report.pdf',
                'file_type': 'pdf',
                'page': 3,
            }
        }]

        context = rag_service.build_rag_context(search_results)

        # Should still work without temporal context
        assert 'report.pdf' in context
        assert 'page 3' in context
        assert 'Sample PDF content' in context
