# file-upload Specification

## Purpose
Provide a complete file upload system that allows users to upload Supply Chain documents (Excel, PDF, Word, PowerPoint, CSV, Text) with validation, temporary storage (MinIO with 24h TTL), and metadata tracking in PostgreSQL.

## ADDED Requirements

### Requirement: File Upload API
The system SHALL provide an API endpoint for uploading files with strict validation and temporary storage.

#### Scenario: User uploads valid Excel file
- **WHEN** a user uploads a .xlsx file via POST /api/files/upload
- **AND** the file size is less than 50MB
- **THEN** the file is validated for MIME type and extension
- **AND** the file is uploaded to MinIO with unique object key (user_id/file_id/filename)
- **AND** file metadata is stored in PostgreSQL files table
- **AND** expires_at is set to now() + 24 hours
- **AND** the response contains file metadata (id, filename, type, size, created_at)

#### Scenario: User uploads file exceeding size limit
- **WHEN** a user uploads a file larger than 50MB
- **THEN** the request is rejected with 413 Payload Too Large
- **AND** an error message explains the size limit
- **AND** no file is stored in MinIO or PostgreSQL

#### Scenario: User uploads unsupported file type
- **WHEN** a user uploads a file with unsupported extension (e.g., .exe, .dmg)
- **THEN** the request is rejected with 415 Unsupported Media Type
- **AND** an error message lists supported formats (.xlsx, .csv, .pdf, .docx, .pptx, .txt)
- **AND** no file is stored

#### Scenario: User uploads file with mismatched extension and MIME type
- **WHEN** a user uploads a file named "document.xlsx" but with PDF MIME type
- **THEN** the request is rejected with 415 Unsupported Media Type
- **AND** an error message indicates MIME type mismatch
- **AND** no file is stored

#### Scenario: User uploads file linked to conversation
- **WHEN** a user uploads a file with conversation_id parameter
- **THEN** the file is linked to that conversation in the files table
- **AND** the file appears in the conversation's file list
- **AND** all conversation participants can access the file

#### Scenario: User uploads file without conversation link
- **WHEN** a user uploads a file without conversation_id parameter
- **THEN** the file is stored with conversation_id = NULL
- **AND** the file can be linked to a conversation later

### Requirement: File Listing API
The system SHALL allow users to list their uploaded files with filtering options.

#### Scenario: User lists all their files
- **WHEN** a user calls GET /api/files
- **THEN** all files belonging to that user are returned
- **AND** files are ordered by created_at DESC (most recent first)
- **AND** each file includes metadata: id, filename, file_type, file_size_bytes, conversation_id, created_at, expires_at, processing_status

#### Scenario: User lists files for specific conversation
- **WHEN** a user calls GET /api/files?conversation_id={id}
- **THEN** only files linked to that conversation are returned
- **AND** files are ordered by created_at DESC

#### Scenario: User lists files with no results
- **WHEN** a user calls GET /api/files and has no uploaded files
- **THEN** an empty array is returned with 200 OK
- **AND** no error is thrown

### Requirement: File Deletion API
The system SHALL allow users to delete their uploaded files before the 24h TTL expires.

#### Scenario: User deletes their own file
- **WHEN** a user calls DELETE /api/files/{file_id}
- **AND** the file belongs to that user
- **THEN** the file is deleted from MinIO storage
- **AND** the file record is deleted from PostgreSQL
- **AND** the response is 204 No Content

#### Scenario: User attempts to delete another user's file
- **WHEN** a user calls DELETE /api/files/{file_id}
- **AND** the file belongs to a different user
- **THEN** the request is rejected with 403 Forbidden
- **AND** an error message indicates insufficient permissions
- **AND** the file is not deleted

#### Scenario: User deletes non-existent file
- **WHEN** a user calls DELETE /api/files/{file_id}
- **AND** the file_id does not exist
- **THEN** the request is rejected with 404 Not Found
- **AND** an error message indicates file not found

### Requirement: File Storage with TTL
The system SHALL automatically purge files from MinIO after 24 hours using lifecycle policies.

#### Scenario: File expires after 24 hours
- **WHEN** 24 hours have elapsed since file upload
- **THEN** the file is automatically deleted from MinIO via lifecycle policy
- **AND** the file record in PostgreSQL is marked as expired (or deleted via pg_cron)
- **AND** subsequent download attempts return 404 Not Found

#### Scenario: File downloaded before expiry
- **WHEN** a user downloads a file before 24h expiry
- **THEN** the file is successfully retrieved from MinIO
- **AND** the file content is returned with correct MIME type
- **AND** the expires_at timestamp is not extended (fixed 24h from upload)

### Requirement: File Upload UI Component
The system SHALL provide a user-friendly file upload interface with drag & drop and file picker.

#### Scenario: User drags file into upload zone
- **WHEN** a user drags a file over the upload zone
- **THEN** the upload zone is visually highlighted (border color change)
- **AND** when the user drops the file, the upload starts immediately
- **AND** a progress bar displays upload percentage
- **AND** the filename and size are displayed during upload

#### Scenario: User clicks upload zone to select file
- **WHEN** a user clicks the upload zone
- **THEN** a file picker dialog opens
- **AND** only supported file types are selectable (.xlsx, .csv, .pdf, .docx, .pptx, .txt)
- **AND** after selection, the upload starts automatically

#### Scenario: Upload completes successfully
- **WHEN** a file upload completes
- **THEN** a success message is displayed
- **AND** the file appears in the conversation's file list with a badge
- **AND** the file badge shows filename and file type icon
- **AND** the upload zone is cleared for next upload

#### Scenario: Upload fails with error
- **WHEN** a file upload fails (size limit, unsupported type, network error)
- **THEN** an error message is displayed explaining the issue
- **AND** the upload progress is hidden
- **AND** the user can retry the upload

#### Scenario: Multiple files uploaded in conversation
- **WHEN** a user uploads multiple files in one conversation
- **THEN** each file is displayed as a separate badge in the chat
- **AND** each badge is clickable to view file details
- **AND** a delete icon appears on hover for each file badge

### Requirement: Rate Limiting
The system SHALL prevent abuse by limiting file upload frequency per user.

#### Scenario: User uploads within rate limit
- **WHEN** a user uploads 9 files in one minute
- **THEN** all uploads succeed normally

#### Scenario: User exceeds upload rate limit
- **WHEN** a user attempts to upload an 11th file within one minute
- **THEN** the request is rejected with 429 Too Many Requests
- **AND** an error message indicates rate limit exceeded
- **AND** the response includes Retry-After header (seconds until reset)

### Requirement: File Processing Status Tracking
The system SHALL track the processing status of uploaded files for downstream operations (parsing, indexing).

#### Scenario: File uploaded but not yet processed
- **WHEN** a file is uploaded
- **THEN** the processing_status field is set to 'pending'
- **AND** the file is queued for processing by document parser

#### Scenario: File processing starts
- **WHEN** the document parser starts processing a file
- **THEN** the processing_status is updated to 'processing'
- **AND** the user sees a "processing" indicator in the UI

#### Scenario: File processing completes successfully
- **WHEN** the document parser completes processing
- **THEN** the processing_status is updated to 'completed'
- **AND** the user sees a "ready" indicator in the UI
- **AND** the file is available for RAG queries

#### Scenario: File processing fails
- **WHEN** the document parser fails to process a file (corrupt file, parsing error)
- **THEN** the processing_status is updated to 'failed'
- **AND** an error message is logged
- **AND** the user sees a "failed" indicator with error details in the UI
- **AND** the file is not available for RAG queries
