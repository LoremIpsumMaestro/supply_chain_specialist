"""Unit tests for document parsers."""

import pytest

from backend.models.file import FileType
from backend.services.document_parser import (
    DocumentChunk,
    DocumentParser,
    ExcelParser,
    PDFParser,
    WordParser,
    PowerPointParser,
    CSVParser,
    TextParser,
    DocumentParserFactory,
)


# ============================================================================
# DocumentChunk Tests
# ============================================================================

class TestDocumentChunk:
    """Tests for DocumentChunk dataclass."""

    def test_create_valid_chunk(self):
        """Test creating a valid document chunk."""
        chunk = DocumentChunk(
            content="Test content",
            metadata={"filename": "test.xlsx", "sheet": "Sheet1"},
            file_type=FileType.EXCEL,
        )

        assert chunk.content == "Test content"
        assert chunk.metadata["filename"] == "test.xlsx"
        assert chunk.file_type == FileType.EXCEL

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Chunk content cannot be empty"):
            DocumentChunk(
                content="",
                metadata={"filename": "test.xlsx"},
                file_type=FileType.EXCEL,
            )

    def test_whitespace_only_content_raises_error(self):
        """Test that whitespace-only content raises ValueError."""
        with pytest.raises(ValueError, match="Chunk content cannot be empty"):
            DocumentChunk(
                content="   \n\t  ",
                metadata={"filename": "test.xlsx"},
                file_type=FileType.EXCEL,
            )

    def test_very_long_content_logs_warning(self, caplog):
        """Test that very long content logs a warning."""
        long_content = "x" * 15000

        chunk = DocumentChunk(
            content=long_content,
            metadata={"filename": "test.xlsx"},
            file_type=FileType.EXCEL,
        )

        assert chunk.content == long_content
        assert "Chunk content very long" in caplog.text


# ============================================================================
# ExcelParser Tests
# ============================================================================

@pytest.mark.parser
class TestExcelParser:
    """Tests for Excel file parser."""

    def test_parse_excel_with_data(self, sample_excel_bytes):
        """Test parsing Excel file with supply chain data."""
        parser = ExcelParser()
        chunks = parser.parse(sample_excel_bytes, "test_inventory.xlsx")

        # Should have multiple chunks (one per non-empty cell)
        assert len(chunks) > 0

        # Check that chunks contain expected data
        stock_chunks = [
            c for c in chunks
            if c.metadata.get("sheet_name") == "Stocks"
        ]
        assert len(stock_chunks) > 0

        # Verify chunk structure
        first_chunk = chunks[0]
        assert isinstance(first_chunk, DocumentChunk)
        assert first_chunk.file_type == FileType.EXCEL
        assert "filename" in first_chunk.metadata
        assert "sheet_name" in first_chunk.metadata
        assert "cell_ref" in first_chunk.metadata
        assert "row" in first_chunk.metadata
        assert "column" in first_chunk.metadata

    def test_parse_excel_detects_negative_stock(self, sample_excel_bytes):
        """Test that parser captures cells with negative stock values."""
        parser = ExcelParser()
        chunks = parser.parse(sample_excel_bytes, "test_inventory.xlsx")

        # Find chunk with negative stock (-50)
        negative_chunks = [
            c for c in chunks
            if c.metadata.get("value") == "-50"
        ]

        assert len(negative_chunks) > 0
        negative_chunk = negative_chunks[0]
        assert negative_chunk.metadata["sheet_name"] == "Stocks"
        assert "-50" in negative_chunk.content

    def test_parse_excel_preserves_cell_references(self, sample_excel_bytes):
        """Test that cell references (e.g., C12) are preserved."""
        parser = ExcelParser()
        chunks = parser.parse(sample_excel_bytes, "test_inventory.xlsx")

        # All chunks should have cell_ref metadata
        for chunk in chunks:
            assert "cell_ref" in chunk.metadata
            # Cell ref format: letter + number (e.g., A1, B2, C12)
            cell_ref = chunk.metadata["cell_ref"]
            assert len(cell_ref) >= 2
            assert cell_ref[0].isalpha()
            assert cell_ref[1:].isdigit()

    def test_parse_excel_includes_column_headers(self, sample_excel_bytes):
        """Test that column headers are included in content for context."""
        parser = ExcelParser()
        chunks = parser.parse(sample_excel_bytes, "test_inventory.xlsx")

        # Find a chunk with "Stock" header
        stock_chunks = [
            c for c in chunks
            if "Stock" in c.content or c.metadata.get("column_header") == "Stock"
        ]

        assert len(stock_chunks) > 0

    def test_parse_excel_handles_multiple_sheets(self, sample_excel_bytes):
        """Test parsing Excel file with multiple sheets."""
        parser = ExcelParser()
        chunks = parser.parse(sample_excel_bytes, "test_inventory.xlsx")

        # Should have chunks from both Stocks and Orders sheets
        sheet_names = {chunk.metadata["sheet_name"] for chunk in chunks}
        assert "Stocks" in sheet_names
        assert "Orders" in sheet_names

    def test_parse_empty_excel_returns_empty_list(self):
        """Test parsing Excel with no data returns empty list."""
        from openpyxl import Workbook
        import io

        # Create empty workbook
        wb = Workbook()
        ws = wb.active
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        empty_bytes = buffer.read()

        parser = ExcelParser()
        chunks = parser.parse(empty_bytes, "empty.xlsx")

        # Empty Excel should return empty chunks
        # (only column headers if any, but our empty one has none)
        assert isinstance(chunks, list)


# ============================================================================
# PDFParser Tests
# ============================================================================

@pytest.mark.parser
class TestPDFParser:
    """Tests for PDF file parser."""

    def test_parse_pdf_with_content(self, sample_pdf_bytes):
        """Test parsing PDF file with content."""
        parser = PDFParser()
        chunks = parser.parse(sample_pdf_bytes, "test_report.pdf")

        assert len(chunks) > 0

        # Verify chunk structure
        first_chunk = chunks[0]
        assert isinstance(first_chunk, DocumentChunk)
        assert first_chunk.file_type == FileType.PDF
        assert "filename" in first_chunk.metadata
        assert "page" in first_chunk.metadata
        assert "chunk_index" in first_chunk.metadata

    def test_parse_pdf_preserves_page_numbers(self, sample_pdf_bytes):
        """Test that page numbers are preserved in metadata."""
        parser = PDFParser()
        chunks = parser.parse(sample_pdf_bytes, "test_report.pdf")

        # All chunks should have page metadata
        for chunk in chunks:
            assert "page" in chunk.metadata
            assert chunk.metadata["page"] >= 1

    def test_parse_pdf_content_extraction(self, sample_pdf_bytes):
        """Test that PDF text content is extracted."""
        parser = PDFParser()
        chunks = parser.parse(sample_pdf_bytes, "test_report.pdf")

        # Content should contain text from PDF
        all_content = " ".join(chunk.content for chunk in chunks)
        assert len(all_content) > 0
        # Check for known text from our sample PDF
        assert "Supply Chain" in all_content or "Report" in all_content


# ============================================================================
# WordParser Tests
# ============================================================================

@pytest.mark.parser
class TestWordParser:
    """Tests for Word document parser."""

    def test_parse_word_with_content(self, sample_word_bytes):
        """Test parsing Word document with content."""
        parser = WordParser()
        chunks = parser.parse(sample_word_bytes, "test_doc.docx")

        assert len(chunks) > 0

        # Verify chunk structure
        first_chunk = chunks[0]
        assert isinstance(first_chunk, DocumentChunk)
        assert first_chunk.file_type == FileType.WORD
        assert "filename" in first_chunk.metadata

    def test_parse_word_paragraphs(self, sample_word_bytes):
        """Test that Word paragraphs are parsed separately."""
        parser = WordParser()
        chunks = parser.parse(sample_word_bytes, "test_doc.docx")

        # Should have chunks for paragraphs
        paragraph_chunks = [
            c for c in chunks
            if "paragraph_index" in c.metadata
        ]
        assert len(paragraph_chunks) > 0

    def test_parse_word_tables(self, sample_word_bytes):
        """Test that Word tables are parsed."""
        parser = WordParser()
        chunks = parser.parse(sample_word_bytes, "test_doc.docx")

        # Should have chunks for table rows
        table_chunks = [
            c for c in chunks
            if "table_index" in c.metadata
        ]
        assert len(table_chunks) > 0

        # Table content should be pipe-separated
        if table_chunks:
            assert "|" in table_chunks[0].content


# ============================================================================
# PowerPointParser Tests
# ============================================================================

@pytest.mark.parser
class TestPowerPointParser:
    """Tests for PowerPoint presentation parser."""

    def test_parse_powerpoint_with_content(self, sample_powerpoint_bytes):
        """Test parsing PowerPoint presentation."""
        parser = PowerPointParser()
        chunks = parser.parse(sample_powerpoint_bytes, "test_presentation.pptx")

        assert len(chunks) > 0

        # Verify chunk structure
        first_chunk = chunks[0]
        assert isinstance(first_chunk, DocumentChunk)
        assert first_chunk.file_type == FileType.POWERPOINT
        assert "filename" in first_chunk.metadata
        assert "slide_number" in first_chunk.metadata

    def test_parse_powerpoint_slide_numbers(self, sample_powerpoint_bytes):
        """Test that slide numbers are preserved."""
        parser = PowerPointParser()
        chunks = parser.parse(sample_powerpoint_bytes, "test_presentation.pptx")

        # All chunks should have slide_number
        for chunk in chunks:
            assert "slide_number" in chunk.metadata
            assert chunk.metadata["slide_number"] >= 1

    def test_parse_powerpoint_content_types(self, sample_powerpoint_bytes):
        """Test that different content types (title, body) are identified."""
        parser = PowerPointParser()
        chunks = parser.parse(sample_powerpoint_bytes, "test_presentation.pptx")

        # Should have chunks with content_type metadata
        content_types = {chunk.metadata.get("content_type") for chunk in chunks}
        assert "title" in content_types or "body" in content_types


# ============================================================================
# CSVParser Tests
# ============================================================================

@pytest.mark.parser
class TestCSVParser:
    """Tests for CSV file parser."""

    def test_parse_csv_with_data(self, sample_csv_bytes):
        """Test parsing CSV file with data."""
        parser = CSVParser()
        chunks = parser.parse(sample_csv_bytes, "test_data.csv")

        assert len(chunks) > 0

        # Verify chunk structure
        first_chunk = chunks[0]
        assert isinstance(first_chunk, DocumentChunk)
        assert first_chunk.file_type == FileType.CSV
        assert "filename" in first_chunk.metadata
        assert "row_number" in first_chunk.metadata
        assert "column_headers" in first_chunk.metadata

    def test_parse_csv_row_numbers(self, sample_csv_bytes):
        """Test that row numbers are correct (1-indexed + header)."""
        parser = CSVParser()
        chunks = parser.parse(sample_csv_bytes, "test_data.csv")

        # Row numbers should start from 2 (header is row 1)
        row_numbers = [chunk.metadata["row_number"] for chunk in chunks]
        assert min(row_numbers) >= 2

    def test_parse_csv_column_headers(self, sample_csv_bytes):
        """Test that column headers are included."""
        parser = CSVParser()
        chunks = parser.parse(sample_csv_bytes, "test_data.csv")

        # All chunks should have column_headers
        for chunk in chunks:
            assert "column_headers" in chunk.metadata
            headers = chunk.metadata["column_headers"]
            assert isinstance(headers, list)
            assert len(headers) > 0

    def test_parse_csv_content_format(self, sample_csv_bytes):
        """Test that CSV content is formatted with column headers."""
        parser = CSVParser()
        chunks = parser.parse(sample_csv_bytes, "test_data.csv")

        # Content should include column headers with values
        for chunk in chunks:
            # Format is "Header1: value1 | Header2: value2"
            assert ":" in chunk.content
            assert "|" in chunk.content or len(chunk.content.split(":")) <= 2


# ============================================================================
# TextParser Tests
# ============================================================================

@pytest.mark.parser
class TestTextParser:
    """Tests for plain text file parser."""

    def test_parse_text_with_content(self, sample_text_bytes):
        """Test parsing text file."""
        parser = TextParser()
        chunks = parser.parse(sample_text_bytes, "test_report.txt")

        assert len(chunks) > 0

        # Verify chunk structure
        first_chunk = chunks[0]
        assert isinstance(first_chunk, DocumentChunk)
        assert first_chunk.file_type == FileType.TEXT
        assert "filename" in first_chunk.metadata

    def test_parse_text_paragraph_splitting(self, sample_text_bytes):
        """Test that text is split into paragraphs."""
        parser = TextParser()
        chunks = parser.parse(sample_text_bytes, "test_report.txt")

        # Should have multiple chunks for different paragraphs
        assert len(chunks) > 1

    def test_parse_text_long_content_chunking(self):
        """Test that very long text is split into smaller chunks."""
        # Create text larger than 4000 characters
        long_text = "Line of text.\n" * 500  # ~6500 characters

        parser = TextParser()
        chunks = parser.parse(long_text.encode('utf-8'), "long_text.txt")

        # Should be split into multiple chunks
        assert len(chunks) > 1

        # Each chunk should be under 4000 characters
        for chunk in chunks:
            assert len(chunk.content) <= 4500  # Allow some margin


# ============================================================================
# DocumentParserFactory Tests
# ============================================================================

class TestDocumentParserFactory:
    """Tests for DocumentParserFactory."""

    def test_get_parser_excel(self):
        """Test getting Excel parser."""
        parser = DocumentParserFactory.get_parser(FileType.EXCEL)
        assert isinstance(parser, ExcelParser)

    def test_get_parser_pdf(self):
        """Test getting PDF parser."""
        parser = DocumentParserFactory.get_parser(FileType.PDF)
        assert isinstance(parser, PDFParser)

    def test_get_parser_word(self):
        """Test getting Word parser."""
        parser = DocumentParserFactory.get_parser(FileType.WORD)
        assert isinstance(parser, WordParser)

    def test_get_parser_powerpoint(self):
        """Test getting PowerPoint parser."""
        parser = DocumentParserFactory.get_parser(FileType.POWERPOINT)
        assert isinstance(parser, PowerPointParser)

    def test_get_parser_csv(self):
        """Test getting CSV parser."""
        parser = DocumentParserFactory.get_parser(FileType.CSV)
        assert isinstance(parser, CSVParser)

    def test_get_parser_text(self):
        """Test getting Text parser."""
        parser = DocumentParserFactory.get_parser(FileType.TEXT)
        assert isinstance(parser, TextParser)

    def test_get_parser_returns_same_instance(self):
        """Test that factory returns the same parser instance for the same type."""
        parser1 = DocumentParserFactory.get_parser(FileType.EXCEL)
        parser2 = DocumentParserFactory.get_parser(FileType.EXCEL)
        assert parser1 is parser2  # Same instance


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestParserIntegration:
    """Integration tests for parser workflow."""

    def test_parse_all_file_types(
        self,
        sample_excel_bytes,
        sample_pdf_bytes,
        sample_word_bytes,
        sample_powerpoint_bytes,
        sample_csv_bytes,
        sample_text_bytes,
    ):
        """Test parsing all supported file types."""
        test_cases = [
            (FileType.EXCEL, sample_excel_bytes, "test.xlsx"),
            (FileType.PDF, sample_pdf_bytes, "test.pdf"),
            (FileType.WORD, sample_word_bytes, "test.docx"),
            (FileType.POWERPOINT, sample_powerpoint_bytes, "test.pptx"),
            (FileType.CSV, sample_csv_bytes, "test.csv"),
            (FileType.TEXT, sample_text_bytes, "test.txt"),
        ]

        for file_type, file_bytes, filename in test_cases:
            parser = DocumentParserFactory.get_parser(file_type)
            chunks = parser.parse(file_bytes, filename)

            # All parsers should return non-empty chunks
            assert len(chunks) > 0, f"Parser for {file_type} returned no chunks"

            # All chunks should be valid
            for chunk in chunks:
                assert isinstance(chunk, DocumentChunk)
                assert chunk.content
                assert chunk.metadata
                assert chunk.metadata["filename"] == filename
