-- Create alerts table for Supply Chain anomaly detection

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    value TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_file_id ON alerts(file_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);

-- Add check constraint for alert_type
ALTER TABLE alerts ADD CONSTRAINT check_alert_type
    CHECK (alert_type IN ('negative_stock', 'date_inconsistency', 'negative_quantity', 'lead_time_outlier'));

-- Add check constraint for severity
ALTER TABLE alerts ADD CONSTRAINT check_severity
    CHECK (severity IN ('critical', 'warning', 'info'));

COMMENT ON TABLE alerts IS 'Supply Chain anomaly alerts detected from uploaded documents';
COMMENT ON COLUMN alerts.alert_type IS 'Type of alert: negative_stock, date_inconsistency, negative_quantity, lead_time_outlier';
COMMENT ON COLUMN alerts.severity IS 'Severity level: critical, warning, info';
COMMENT ON COLUMN alerts.metadata IS 'JSON metadata with source information (cell_ref, page, sheet_name, etc.)';
COMMENT ON COLUMN alerts.value IS 'The problematic value that triggered the alert';
