# Spec: Temporal Analysis

## ADDED Requirements

### Requirement: System Date Injection
The LLM service SHALL automatically inject the current system date into every LLM prompt in French natural language format.

#### Scenario: Date appears in LLM context
- **WHEN** the LLM generates a response for any user query
- **THEN** the system prompt SHALL include the current date in format "DD Month YYYY" (example: "29 janvier 2026")
- **AND** the date SHALL be inserted before the RAG context section

#### Scenario: Date enables temporal reasoning
- **WHEN** a user asks "Is this delivery late?"
- **AND** the document contains a delivery date of "15 janvier 2026"
- **AND** the current date is "29 janvier 2026"
- **THEN** the LLM SHALL use the injected date to calculate that the delivery is 14 days late
- **AND** the response SHALL mention the specific delay

---

### Requirement: Temporal Column Detection
The document processing service SHALL automatically detect date/datetime columns in Excel and CSV files using heuristic patterns.

#### Scenario: Detect date columns by name
- **WHEN** an Excel file contains columns named "date_commande" and "date_livraison"
- **THEN** the system SHALL detect both columns as temporal columns
- **AND** store them in `temporal_metadata.detected_date_columns`

#### Scenario: Validate column content format
- **WHEN** a column named "date" contains values "01/02/2025", "15/03/2025", "30/04/2025"
- **THEN** the system SHALL parse the values as dates (DD/MM/YYYY format)
- **AND** mark the column as temporal if ≥80% of non-empty cells are valid dates

#### Scenario: Ignore non-temporal date columns
- **WHEN** a column is named "created_at" or "updated_at" or "deleted_at"
- **THEN** the system SHALL NOT detect it as a temporal column (blacklist pattern)

#### Scenario: Insufficient data coverage
- **WHEN** a column named "date_optional" has valid dates in only 5% of rows
- **THEN** the system SHALL NOT detect it as a temporal column
- **AND** log a warning about sparse temporal data

---

### Requirement: Lead Time Calculation
The temporal service SHALL automatically calculate lead times (delays) between paired date columns.

#### Scenario: Auto-detect lead time pair
- **WHEN** a file has exactly 2 detected temporal columns: "date_commande" and "date_livraison"
- **THEN** the system SHALL assume the pair represents (start, end) dates
- **AND** calculate lead time in days: `date_livraison - date_commande`
- **AND** store statistics (mean, median, max, outliers) in `temporal_metadata.lead_time_stats`

#### Scenario: Multiple temporal columns
- **WHEN** a file has 4 detected columns: "order_date", "ship_date", "delivery_date", "received_date"
- **THEN** the system SHALL identify pairs using common patterns:
  - `(order_date, delivery_date)` → Order lead time
  - `(ship_date, received_date)` → Transit time
- **AND** store all calculated pairs in `temporal_metadata`

#### Scenario: Ambiguous columns require manual config
- **WHEN** a file has 3 columns: "date_a", "date_b", "date_c" with no recognizable patterns
- **THEN** the system SHALL NOT auto-calculate lead times
- **AND** set `temporal_metadata.user_configured_columns = null` (requires manual config)

#### Scenario: Outlier detection
- **WHEN** lead times are calculated for 100 orders
- **AND** 98 orders have lead times between 5-20 days
- **AND** 2 orders have lead times of 45 and 38 days
- **THEN** the system SHALL flag the 2 outliers in `temporal_metadata.lead_time_stats.outliers`

---

### Requirement: Time Range Extraction
The temporal service SHALL extract the earliest and latest dates from all temporal columns to define the data time range.

#### Scenario: Extract time range
- **WHEN** an Excel file has temporal data spanning from "2025-06-01" to "2026-01-15"
- **THEN** the system SHALL store `temporal_metadata.time_range = {earliest: "2025-06-01", latest: "2026-01-15"}`
- **AND** the LLM context SHALL include this range (example: "Les données couvrent la période du 1 juin 2025 au 15 janvier 2026")

#### Scenario: Invalid dates are skipped
- **WHEN** a temporal column contains "2025-02-30" (invalid date)
- **THEN** the system SHALL skip this value
- **AND** log a warning
- **AND** calculate time range using only valid dates

---

### Requirement: Trend and Seasonality Analysis
The temporal service SHALL calculate trends and seasonal patterns for time series data (minimum 6 months).

#### Scenario: Calculate rolling averages
- **WHEN** a CSV file has monthly sales data for 12 months
- **AND** a user query asks about "tendances"
- **THEN** the system SHALL calculate 7-day and 30-day rolling averages
- **AND** enrich chunk metadata with `temporal_context.rolling_avg_7d` and `temporal_context.rolling_avg_30d`

#### Scenario: Detect monthly variation
- **WHEN** sales data shows December value = 250 and November value = 200
- **THEN** the system SHALL calculate variation: `+25%`
- **AND** store in chunk metadata: `temporal_context.vs_previous_month = "+25%"`

#### Scenario: Identify seasonal patterns
- **WHEN** sales data spans 12 months (June 2025 - May 2026)
- **AND** December shows a peak (30% above yearly average)
- **THEN** the system SHALL detect seasonal pattern
- **AND** enrich metadata: `temporal_context.seasonal_pattern = "Pic annuel (décembre)"`

#### Scenario: Insufficient data for seasonality
- **WHEN** a file contains only 3 months of data
- **THEN** the system SHALL NOT attempt seasonality detection
- **AND** log "Insufficient data for seasonal analysis (minimum: 6 months)"

---

### Requirement: Temporal Metadata Enrichment
Document chunks SHALL be enriched with temporal context metadata when temporal columns are detected.

#### Scenario: Enrich Excel chunk with temporal context
- **WHEN** an Excel chunk is created from cell C12 (sheet "Sales", value 150, date column "2025-12-15")
- **THEN** the chunk metadata SHALL include:
  ```json
  {
    "filename": "sales.xlsx",
    "sheet_name": "Sales",
    "cell_ref": "C12",
    "value": 150,
    "temporal_context": {
      "date": "2025-12-15",
      "rolling_avg_7d": 145,
      "rolling_avg_30d": 120,
      "vs_previous_month": "+25%",
      "seasonal_pattern": "Pic annuel (décembre)"
    }
  }
  ```

#### Scenario: No temporal context for non-temporal data
- **WHEN** a PDF document has no temporal columns (text-only)
- **THEN** chunk metadata SHALL NOT include `temporal_context`
- **AND** only the system date injection SHALL provide temporal awareness

---

### Requirement: Manual Temporal Configuration
Users SHALL be able to manually configure temporal columns if automatic detection fails or is incorrect.

#### Scenario: User corrects detected columns
- **WHEN** automatic detection identifies "update_date" as a temporal column (false positive)
- **AND** the user sends PATCH `/api/files/{file_id}/temporal-config` with `{"date_columns": ["order_date", "delivery_date"]}`
- **THEN** the system SHALL override `temporal_metadata.detected_date_columns` with user-provided columns
- **AND** set `temporal_metadata.user_configured_columns = ["order_date", "delivery_date"]`
- **AND** trigger re-indexing of document chunks with new temporal context

#### Scenario: User specifies lead time pairs
- **WHEN** a file has ambiguous columns: "date_a", "date_b", "date_c"
- **AND** the user sends PATCH with `{"lead_time_pairs": [["date_a", "date_c"]]}`
- **THEN** the system SHALL calculate lead times for the specified pair
- **AND** update `temporal_metadata.lead_time_stats`

#### Scenario: Retrieve temporal configuration
- **WHEN** the user sends GET `/api/files/{file_id}/temporal-metadata`
- **THEN** the system SHALL return the complete `temporal_metadata` object
- **AND** include detected columns, user overrides, time range, and lead time stats

---

### Requirement: Performance Requirements
Temporal analysis SHALL NOT add more than 500ms latency to the document processing pipeline.

#### Scenario: Fast detection on medium files
- **WHEN** an Excel file has 1000 rows × 10 columns
- **THEN** temporal column detection SHALL complete in ≤200ms

#### Scenario: Sampling for large files
- **WHEN** an Excel file has 50,000 rows × 15 columns
- **THEN** the system SHALL sample only the first 1000 rows for detection
- **AND** complete detection in ≤300ms

#### Scenario: Timeout for complex calculations
- **WHEN** trend calculation takes >5 seconds
- **THEN** the system SHALL timeout and skip trend analysis
- **AND** log "Temporal analysis timeout, skipping trends"
- **AND** continue with basic temporal metadata (time range, detected columns)
