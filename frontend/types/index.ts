/**
 * Type definitions for the Supply Chain AI Assistant frontend.
 */

export interface Conversation {
  id: string
  user_id: string
  title: string | null
  created_at: string
  updated_at: string
  expires_at: string
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[]
}

export type MessageRole = 'user' | 'assistant'

export interface CitationMetadata {
  filename: string
  sheet_name?: string // For Excel files
  cell_ref?: string // For Excel (e.g., "C12")
  page?: number // For PDF/Word/PowerPoint
  row?: number // For Excel
  column?: number // For Excel
  value?: string // The actual value from source
}

export interface Message {
  id: string
  conversation_id: string
  role: MessageRole
  content: string
  citations?: CitationMetadata[]
  created_at: string
}

export interface MessageStreamChunk {
  content: string
  is_final: boolean
  citations?: CitationMetadata[]
  error?: string
}

export interface SendMessageRequest {
  content: string
}

// File types
export type FileType = 'excel' | 'csv' | 'pdf' | 'word' | 'powerpoint' | 'text'
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface FileUpload {
  id: string
  user_id: string
  conversation_id: string | null
  filename: string
  file_type: FileType
  file_size_bytes: number
  processing_status: ProcessingStatus
  created_at: string
  expires_at: string
}

// Alert types
export type AlertType = 'negative_stock' | 'date_inconsistency' | 'negative_quantity' | 'lead_time_outlier'
export type AlertSeverity = 'critical' | 'warning' | 'info'

export interface Alert {
  id: string
  user_id: string
  file_id: string
  conversation_id: string | null
  alert_type: AlertType
  severity: AlertSeverity
  message: string
  metadata: Record<string, any>
  created_at: string
}

// Auth types
export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}
