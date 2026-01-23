-- Migration: Setup pg_cron for automatic data purge
-- Version: 002
-- Description: Configure pg_cron to purge expired conversations every hour

-- Enable pg_cron extension (requires superuser privileges)
-- Note: This may need to be run manually by a database administrator
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Create purge function
CREATE OR REPLACE FUNCTION purge_expired_conversations()
RETURNS void AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired conversations (messages cascade automatically)
    DELETE FROM conversations
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Log the purge operation
    RAISE NOTICE 'Purged % expired conversations at %', deleted_count, NOW();
END;
$$ LANGUAGE plpgsql;

-- Schedule purge job to run every hour
-- Note: This requires pg_cron to be properly configured in postgresql.conf
-- Add: shared_preload_libraries = 'pg_cron'
SELECT cron.schedule(
    'purge-expired-conversations',
    '0 * * * *',  -- Every hour at minute 0
    'SELECT purge_expired_conversations();'
);

-- Comments for documentation
COMMENT ON FUNCTION purge_expired_conversations IS 'Deletes conversations that have passed their 24-hour expiration time';
