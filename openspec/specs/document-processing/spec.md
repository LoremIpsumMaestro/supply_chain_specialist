# document-processing Specification

## Purpose
TBD - created by archiving change implement-mvp-features. Update Purpose after archive.
## Requirements
### Requirement: Excel Document Parsing
Excel parser SHALL detect temporal columns and enrich chunks with temporal metadata.

**Changes from original**: Added temporal column detection and metadata enrichment.

#### Scenario: Parse Excel with temporal enrichment
- **WHEN** an Excel file is parsed with columns "date_commande" and "quantite"
- **THEN** the parser SHALL detect "date_commande" as a temporal column
- **AND** enrich each chunk's metadata with the corresponding date value
- **AND** include `temporal_context.date` in chunk metadata

#### Scenario: Excel chunk with lead time calculation
- **WHEN** an Excel file has both "date_commande" and "date_livraison" columns
- **AND** row 12 has values: date_commande="2025-12-01", date_livraison="2025-12-15"
- **THEN** the chunk for row 12 SHALL include in metadata:
  ```json
  {
    "temporal_context": {
      "date_commande": "2025-12-01",
      "date_livraison": "2025-12-15",
      "lead_time_days": 14
    }
  }
  ```

#### Scenario: Skip blacklisted temporal columns
- **WHEN** an Excel file has columns "created_at", "updated_at", "date_commande"
- **THEN** the parser SHALL detect only "date_commande" as a temporal column
- **AND** ignore "created_at" and "updated_at" (blacklist pattern)

---

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
CSV parser SHALL detect temporal columns using dateutil parsing and enrich chunks.

**Changes from original**: Added temporal column detection for CSV files.

#### Scenario: Detect dates in CSV with mixed formats
- **WHEN** a CSV column "delivery_date" contains values "01/02/2025", "2025-03-15", "15-04-2025"
- **THEN** the parser SHALL detect the column as temporal
- **AND** normalize all dates to ISO format (YYYY-MM-DD)
- **AND** enrich chunk metadata with `temporal_context.delivery_date`

#### Scenario: CSV with time series data
- **WHEN** a CSV has columns "month" and "sales_amount"
- **AND** "month" contains "2025-01", "2025-02", "2025-03", ... "2025-12"
- **THEN** the parser SHALL detect "month" as temporal
- **AND** trigger trend analysis (rolling averages, variation)
- **AND** enrich chunks with `temporal_context.rolling_avg_30d` and `temporal_context.vs_previous_month`

---

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
All document chunks SHALL include upload date and temporal metadata when applicable.

**Changes from original**: Added upload_date and temporal_context to required metadata.

#### Scenario: Chunk metadata includes upload date
- **WHEN** any document is parsed (Excel, PDF, CSV, Word, PowerPoint, Text)
- **THEN** ALL chunks SHALL include `metadata.upload_date` with ISO timestamp
- **AND** format: "2026-01-29T10:30:00Z"

#### Scenario: Temporal metadata present for Excel/CSV
- **WHEN** an Excel or CSV chunk is created from a row with detected temporal columns
- **THEN** the metadata SHALL include `temporal_context` object
- **AND** include detected date values, lead times (if calculated), and trends (if available)

#### Scenario: No temporal context for non-temporal documents
- **WHEN** a PDF or Word document has no detected temporal patterns
- **THEN** chunk metadata SHALL NOT include `temporal_context`
- **AND** SHALL still include `metadata.upload_date`

