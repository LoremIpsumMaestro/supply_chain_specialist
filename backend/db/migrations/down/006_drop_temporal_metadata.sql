-- Rollback: Remove temporal_metadata field from files table

-- Drop index
DROP INDEX IF EXISTS idx_files_temporal_metadata;

-- Drop column
ALTER TABLE files DROP COLUMN IF EXISTS temporal_metadata;
