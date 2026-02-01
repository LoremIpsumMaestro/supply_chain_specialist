# Spec Delta: Document Processing

## MODIFIED Requirements

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
