# alert-mode Specification

## Purpose
Automatically detect Supply Chain operational inconsistencies and anomalies in uploaded documents to provide proactive alerts to users. Supports MVP requirement "Mode Alerte: Détection d'incohérences de base (stocks négatifs, dates incohérentes)".

## ADDED Requirements

### Requirement: Negative Stock Detection
The system SHALL detect negative stock values in uploaded documents and alert users.

#### Scenario: Detect negative stock in Excel file
- **WHEN** an Excel file is parsed and contains a cell with a negative numeric value
- **AND** the cell is in a column with header matching "stock", "inventory", "quantity", "qty", "quantité"
- **THEN** an alert is created with:
  - `type`: "negative_stock"
  - `severity`: "critical"
  - `message`: "Stock négatif détecté: -50 unités"
  - `source`: CitationMetadata (filename, sheet, cell_ref, value)
- **AND** the alert is stored in the alerts table

#### Scenario: Detect negative stock in CSV file
- **WHEN** a CSV file contains a row with negative value in stock-related column
- **THEN** an alert is created with row_number metadata
- **AND** the alert includes column header context

#### Scenario: No negative stock found
- **WHEN** all stock values in a document are >= 0
- **THEN** no negative stock alert is created
- **AND** processing continues normally

#### Scenario: Negative stock threshold configurable
- **WHEN** the system detects stock values
- **THEN** the threshold for "negative" can be configured (default: < 0)
- **AND** configuration can be adjusted to detect "low stock" (< 10) as warning severity

### Requirement: Date Inconsistency Detection
The system SHALL detect illogical date sequences in Supply Chain data (e.g., delivery before order).

#### Scenario: Detect delivery date before order date
- **WHEN** a document contains both order_date and delivery_date fields
- **AND** delivery_date < order_date
- **THEN** an alert is created with:
  - `type`: "date_inconsistency"
  - `severity`: "high"
  - `message`: "Date de livraison (2024-01-10) antérieure à la date de commande (2024-01-15)"
  - `source`: CitationMetadata with both date cells/fields

#### Scenario: Detect order date in the future
- **WHEN** a document contains an order_date field
- **AND** order_date > current date + 1 year
- **THEN** an alert is created with severity "warning"
- **AND** message indicates suspicious future date

#### Scenario: Detect negative lead time
- **WHEN** a document contains expected_delivery_date and actual_delivery_date
- **AND** actual_delivery_date < expected_delivery_date by more than 30 days
- **THEN** an alert is created for "early delivery anomaly" (may indicate data error)

#### Scenario: Valid date sequence
- **WHEN** order_date < delivery_date < payment_date
- **THEN** no date inconsistency alert is created

### Requirement: Negative Quantity Detection
The system SHALL detect negative quantities in orders, shipments, or invoices.

#### Scenario: Detect negative order quantity
- **WHEN** a document contains order quantity < 0
- **AND** the field matches patterns: "order_qty", "quantity_ordered", "quantité_commandée"
- **THEN** an alert is created with:
  - `type`: "negative_quantity"
  - `severity`: "critical"
  - `message`: "Quantité commandée négative: -10"

#### Scenario: Detect negative shipment quantity
- **WHEN** a shipment record has negative quantity
- **THEN** an alert is created with context about shipment ID/reference

#### Scenario: Zero quantity in critical fields
- **WHEN** a field like "quantity_ordered" is exactly 0
- **THEN** a warning alert is created (may be valid but unusual)

### Requirement: Lead Time Outlier Detection
The system SHALL detect abnormally long or short lead times that may indicate data errors.

#### Scenario: Detect abnormally long lead time
- **WHEN** a document contains order_date and delivery_date
- **AND** delivery_date - order_date > 90 days (configurable threshold)
- **THEN** an alert is created with:
  - `type`: "lead_time_outlier"
  - `severity`: "warning"
  - `message`: "Délai de livraison anormalement long: 120 jours"

#### Scenario: Detect abnormally short lead time
- **WHEN** delivery_date - order_date < 1 day for non-local orders
- **THEN** a warning alert is created (may indicate same-day order-delivery data error)

#### Scenario: Lead time within normal range
- **WHEN** lead time is between 1 and 90 days
- **THEN** no outlier alert is created

#### Scenario: Statistical outlier detection
- **WHEN** a file contains 100+ lead time values
- **THEN** statistical outliers (beyond 2 standard deviations) are flagged
- **AND** alerts include context: "Lead time of 150 days is 3.2 std deviations above mean of 30 days"

### Requirement: Alert Storage and Retrieval
The system SHALL store detected alerts in PostgreSQL and provide API access.

#### Scenario: Alerts stored after document processing
- **WHEN** document processing detects 3 alerts
- **THEN** all 3 alerts are inserted into the alerts table with:
  - `id`: UUID
  - `user_id`: file owner
  - `file_id`: source file
  - `conversation_id`: linked conversation (if any)
  - `alert_type`: enum (negative_stock, date_inconsistency, etc.)
  - `severity`: enum (critical, high, warning, info)
  - `message`: user-friendly French text
  - `metadata`: JSONB with source citation and values
  - `created_at`: timestamp

#### Scenario: Retrieve alerts for file
- **WHEN** a user calls GET /api/files/{file_id}/alerts
- **THEN** all alerts for that file are returned
- **AND** alerts are ordered by severity (critical first), then created_at

#### Scenario: Retrieve alerts for conversation
- **WHEN** a user calls GET /api/conversations/{id}/alerts
- **THEN** all alerts from all files in that conversation are returned
- **AND** alerts include file context (filename)

#### Scenario: User without alerts
- **WHEN** a user's documents have no detected alerts
- **THEN** GET /api/files/{file_id}/alerts returns empty array with 200 OK

### Requirement: Alert Display in UI
The system SHALL display alerts prominently in the chat interface with visual severity indicators.

#### Scenario: Display critical alert badge
- **WHEN** a file with critical alerts is uploaded
- **THEN** a red alert badge appears next to the file in the chat
- **AND** the badge shows: "🚨 3 alertes critiques"
- **AND** clicking the badge expands alert details

#### Scenario: Display warning alert badge
- **WHEN** a file has only warning-level alerts
- **THEN** an orange alert badge appears
- **AND** the badge shows: "⚠️ 2 alertes"

#### Scenario: Alert detail tooltip
- **WHEN** a user hovers over an alert badge
- **THEN** a tooltip shows the first 3 alert messages
- **AND** if more than 3 alerts exist, shows "...and 5 more"

#### Scenario: Expanded alert list
- **WHEN** a user clicks an alert badge
- **THEN** a modal or expandable section shows all alerts with:
  - Severity icon (🚨 critical, ⚠️ warning, ℹ️ info)
  - Message text
  - Source citation (clickable to view in document if possible)
  - Timestamp

#### Scenario: Alert notification after upload
- **WHEN** file processing completes and alerts are detected
- **THEN** a system message appears in chat:
  - "⚠️ Analyse terminée: 2 alertes détectées dans production.xlsx. Cliquez pour voir les détails."
- **AND** the message is styled differently from normal chat messages

### Requirement: Alert Rules Configuration
The system SHALL allow configurable thresholds and rules for alert detection.

#### Scenario: Configure lead time thresholds
- **WHEN** an admin configures alert rules
- **THEN** thresholds can be set per alert type:
  - `lead_time_long`: 90 days (default)
  - `lead_time_short`: 1 day (default)
  - `low_stock_threshold`: 10 units (default)
- **AND** configuration is stored in database or environment variables

#### Scenario: Disable specific alert types
- **WHEN** an alert type is disabled in configuration
- **THEN** that alert type is not detected during document processing
- **AND** existing alerts of that type remain in database

#### Scenario: Custom alert rules (V1 feature preview)
- **WHEN** a user wants custom rules (e.g., "alert if price > $1000")
- **THEN** the system logs a feature request
- **AND** custom rules are planned for V1 phase

### Requirement: Alert Performance
The system SHALL detect alerts efficiently without significantly delaying document processing.

#### Scenario: Alert detection runs in parallel with indexing
- **WHEN** document chunks are generated
- **THEN** alert detection runs concurrently with RAG indexing
- **AND** alert detection completes within 2 seconds for files with < 1000 rows

#### Scenario: Large file alert detection
- **WHEN** an Excel file has 10,000 rows
- **THEN** alert detection completes within 10 seconds
- **AND** processing is not blocked by alert detection

### Requirement: Alert Logging and Monitoring
The system SHALL log alert detection events for monitoring and tuning.

#### Scenario: Log alert detection summary
- **WHEN** document processing completes
- **THEN** a log entry is created with:
  - file_id
  - alert counts by type and severity
  - processing duration
- **AND** logs are structured JSON for Prometheus/Grafana (V1)

#### Scenario: Alert false positive rate tracking
- **WHEN** users provide feedback on alerts (V1 feature)
- **THEN** false positive rate is calculated per alert type
- **AND** thresholds are adjusted if false positive rate > 30%
