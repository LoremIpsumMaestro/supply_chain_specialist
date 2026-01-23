-- Migration 003: Create files table for uploaded documents
-- This table tracks metadata for files stored in MinIO

CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- excel, pdf, word, powerpoint, csv, text
    file_size_bytes INTEGER NOT NULL,
    minio_object_key VARCHAR(500) NOT NULL,  -- user_id/file_id/filename
    processing_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_files_user CHECK (user_id IS NOT NULL)
);

-- Indexes for performance
CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_files_conversation_id ON files(conversation_id) WHERE conversation_id IS NOT NULL;
CREATE INDEX idx_files_expires_at ON files(expires_at);
CREATE INDEX idx_files_processing_status ON files(processing_status);

-- Comments for documentation
COMMENT ON TABLE files IS 'Stores metadata for uploaded Supply Chain documents with 24h TTL';
COMMENT ON COLUMN files.minio_object_key IS 'S3-compatible object key in MinIO storage';
COMMENT ON COLUMN files.processing_status IS 'Status: pending (uploaded), processing (parsing), completed (indexed), failed (error)';
COMMENT ON COLUMN files.expires_at IS 'Automatic deletion after 24 hours for confidentiality';
