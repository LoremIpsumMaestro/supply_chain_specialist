-- Migration: Add temporal_metadata field to files table
-- Purpose: Store temporal analysis results for Excel/CSV files

-- Add temporal_metadata JSONB column
ALTER TABLE files ADD COLUMN temporal_metadata JSONB;

-- Create GIN index for efficient JSONB queries
CREATE INDEX idx_files_temporal_metadata ON files USING GIN (temporal_metadata);

-- Add comment for documentation
COMMENT ON COLUMN files.temporal_metadata IS 'Temporal analysis metadata including detected date columns, time range, and lead time statistics';
