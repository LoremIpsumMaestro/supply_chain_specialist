# document-processing Specification

## Purpose
Extract structured text with precise metadata from uploaded Supply Chain documents (Excel, PDF, Word, PowerPoint, CSV, Text) for RAG indexing and alert detection. Provide cell-level granularity for Excel files to enable accurate citations like "Selon la cellule C12 (feuille 'Stocks' du fichier production.xlsx)".

## ADDED Requirements

### Requirement: Excel Document Parsing
The system SHALL parse Excel files cell-by-cell with sheet, row, column, and cell reference metadata.

#### Scenario: Parse Excel file with multiple sheets
- **WHEN** an Excel file with 3 sheets is processed
- **THEN** all non-empty cells from all sheets are extracted
- **AND** each cell generates one DocumentChunk with metadata:
  ```json
  {
    "filename": "production.xlsx",
    "file_type": "excel",
    "sheet_name": "Stocks",
    "cell_ref": "C12",
    "row": 12,
    "column": 3,
    "value": "150"
  }
  ```
- **AND** empty cells are skipped

#### Scenario: Parse Excel cell with formula
- **WHEN** a cell contains a formula (e.g., =SUM(A1:A10))
- **THEN** the displayed value is extracted (not the formula)
- **AND** the chunk content contains the calculated result

#### Scenario: Parse Excel merged cells
- **WHEN** a range of cells is merged (e.g., A1:C1)
- **THEN** one DocumentChunk is created for the merged cell
- **AND** the cell_ref references the top-left cell (A1)
- **AND** the metadata indicates merged range if available

#### Scenario: Parse Excel with headers
- **WHEN** the first row contains column headers
- **THEN** the header names are included in chunk metadata
- **AND** data rows reference their column headers for context

#### Scenario: Parse Excel with numeric formatting
- **WHEN** a cell contains formatted numbers (e.g., currency, percentages)
- **THEN** the displayed formatted value is extracted
- **AND** the raw numeric value is also stored in metadata if available

### Requirement: PDF Document Parsing
The system SHALL parse PDF files page-by-page with chunking for long pages.

#### Scenario: Parse multi-page PDF
- **WHEN** a PDF with 10 pages is processed
- **THEN** text is extracted from each page
- **AND** each page generates at least one DocumentChunk with metadata:
  ```json
  {
    "filename": "rapport.pdf",
    "file_type": "pdf",
    "page": 3,
    "chunk_index": 0
  }
  ```

#### Scenario: Parse PDF page exceeding token limit
- **WHEN** a PDF page contains more than 1000 tokens of text
- **THEN** the page is split into multiple chunks by paragraph breaks
- **AND** each chunk has chunk_index (0, 1, 2...)
- **AND** each chunk is less than 1000 tokens

#### Scenario: Parse PDF with no extractable text (scanned image)
- **WHEN** a PDF contains only scanned images with no OCR text
- **THEN** the parser extracts empty or minimal text
- **AND** the processing_status is set to 'completed' (not 'failed')
- **AND** a warning is logged indicating low text content

#### Scenario: Parse corrupted PDF
- **WHEN** a PDF file is corrupted and cannot be parsed
- **THEN** the parser raises an exception
- **AND** the processing_status is set to 'failed'
- **AND** an error message is stored for user feedback

### Requirement: Word Document Parsing
The system SHALL parse Word files paragraph-by-paragraph.

#### Scenario: Parse Word document with paragraphs
- **WHEN** a Word file with 50 paragraphs is processed
- **THEN** each non-empty paragraph generates one DocumentChunk
- **AND** each chunk includes metadata:
  ```json
  {
    "filename": "contrat.docx",
    "file_type": "word",
    "paragraph_index": 12
  }
  ```

#### Scenario: Parse Word document with tables
- **WHEN** a Word file contains tables
- **THEN** table cells are extracted as separate paragraphs
- **AND** table structure metadata is included (row, column) if available

#### Scenario: Parse Word document with headers/footers
- **WHEN** a Word file contains headers and footers
- **THEN** header/footer text is extracted separately
- **AND** metadata indicates content type (header/footer/body)

### Requirement: PowerPoint Document Parsing
The system SHALL parse PowerPoint files slide-by-slide.

#### Scenario: Parse PowerPoint presentation
- **WHEN** a PowerPoint file with 20 slides is processed
- **THEN** each slide generates one or more DocumentChunks (title + body)
- **AND** each chunk includes metadata:
  ```json
  {
    "filename": "presentation.pptx",
    "file_type": "powerpoint",
    "slide_number": 5,
    "content_type": "title" // or "body"
  }
  ```

#### Scenario: Parse PowerPoint slide with bullet points
- **WHEN** a slide contains bullet points
- **THEN** all bullet text is combined into one chunk for the slide body
- **AND** bullet structure is preserved in the text

#### Scenario: Parse PowerPoint with notes
- **WHEN** a slide contains speaker notes
- **THEN** notes are extracted as separate chunks
- **AND** metadata indicates content_type: "notes"

### Requirement: CSV Document Parsing
The system SHALL parse CSV files row-by-row with column header context.

#### Scenario: Parse CSV with headers
- **WHEN** a CSV file with headers in the first row is processed
- **THEN** each data row generates one DocumentChunk
- **AND** each chunk includes metadata:
  ```json
  {
    "filename": "stocks.csv",
    "file_type": "csv",
    "row_number": 15,
    "column_headers": ["Product", "Quantity", "Location"]
  }
  ```
- **AND** the chunk content includes column headers for context

#### Scenario: Parse CSV without headers
- **WHEN** a CSV file has no headers (only data rows)
- **THEN** each row is parsed with numeric column indexes
- **AND** column_headers metadata contains ["Column_1", "Column_2", ...]

#### Scenario: Parse CSV with quoted fields
- **WHEN** a CSV file contains fields with commas in quotes ("Paris, France")
- **THEN** quoted fields are parsed correctly without splitting on internal commas

### Requirement: Text Document Parsing
The system SHALL parse plain text files with line or paragraph-based chunking.

#### Scenario: Parse text file line-by-line
- **WHEN** a text file is processed
- **THEN** the text is split into chunks by line or paragraph breaks
- **AND** each chunk is less than 1000 tokens
- **AND** each chunk includes metadata:
  ```json
  {
    "filename": "notes.txt",
    "file_type": "text",
    "line_number": 42
  }
  ```

#### Scenario: Parse large text file
- **WHEN** a text file contains more than 10,000 lines
- **THEN** the file is chunked into manageable segments (< 1000 tokens each)
- **AND** line numbers are preserved in metadata

### Requirement: Asynchronous Document Processing
The system SHALL process uploaded documents asynchronously using Celery task queue.

#### Scenario: File upload triggers processing job
- **WHEN** a file upload completes (POST /api/files/upload)
- **THEN** a Celery task is enqueued to process the document
- **AND** the file processing_status is set to 'pending'
- **AND** the API response is returned immediately (non-blocking)

#### Scenario: Processing job executes successfully
- **WHEN** the Celery task starts processing a file
- **THEN** the file is downloaded from MinIO
- **AND** the appropriate parser is selected based on file_type
- **AND** all chunks are extracted with metadata
- **AND** the processing_status is updated to 'completed'
- **AND** chunks are passed to RAG indexing (next stage)

#### Scenario: Processing job fails with parser error
- **WHEN** the parser encounters an error (corrupt file, unsupported format variant)
- **THEN** the exception is caught and logged
- **AND** the processing_status is updated to 'failed'
- **AND** the error message is stored for user feedback
- **AND** the file is not passed to RAG indexing

#### Scenario: Processing job retries on transient error
- **WHEN** the processing job fails due to transient error (MinIO timeout, network issue)
- **THEN** the task is retried up to 3 times with exponential backoff
- **AND** if all retries fail, the processing_status is set to 'failed'

### Requirement: Chunking Strategy
The system SHALL apply intelligent chunking to balance citation precision and context richness.

#### Scenario: Excel chunking preserves cell granularity
- **WHEN** an Excel file is chunked
- **THEN** each non-empty cell is one chunk (maximum granularity)
- **AND** no cells are merged into larger chunks

#### Scenario: PDF/Word chunking respects semantic boundaries
- **WHEN** a PDF or Word document is chunked
- **THEN** chunks are split at paragraph or sentence boundaries
- **AND** no chunk exceeds 1000 tokens
- **AND** no sentence is split across multiple chunks

#### Scenario: CSV chunking preserves row integrity
- **WHEN** a CSV file is chunked
- **THEN** each row is one chunk (never split)
- **AND** column headers are included in each chunk for context

### Requirement: Metadata Completeness
The system SHALL include all necessary metadata for accurate citation generation.

#### Scenario: Chunk metadata enables precise citations
- **WHEN** a chunk is generated by any parser
- **THEN** the metadata includes:
  - filename (original filename)
  - file_type (excel, pdf, word, powerpoint, csv, text)
  - source-specific fields (sheet_name, cell_ref, page, slide_number, etc.)
  - value or text content
- **AND** the metadata is sufficient to generate a citation like:
  - "Selon la cellule C12 (feuille 'Stocks' du fichier production.xlsx): 150"
  - "D'après la page 3 du fichier rapport.pdf: ..."

#### Scenario: Chunk content includes context
- **WHEN** a chunk is extracted from a structured document (Excel, CSV)
- **THEN** the chunk content includes surrounding context (e.g., row headers, column names)
- **AND** the context enables LLM to understand the meaning without requiring additional chunks
