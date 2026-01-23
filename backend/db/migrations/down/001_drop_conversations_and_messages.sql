-- Rollback Migration: Drop conversations and messages tables
-- Version: 001
-- Description: Rollback schema for chat interface

-- Drop trigger
DROP TRIGGER IF EXISTS trigger_update_conversation_timestamp ON messages;

-- Drop function
DROP FUNCTION IF EXISTS update_conversation_updated_at();

-- Drop indexes
DROP INDEX IF EXISTS idx_messages_created_at;
DROP INDEX IF EXISTS idx_messages_conversation_id;
DROP INDEX IF EXISTS idx_conversations_updated_at;
DROP INDEX IF EXISTS idx_conversations_expires_at;
DROP INDEX IF EXISTS idx_conversations_user_id;

-- Drop tables (cascade will drop dependent messages)
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
