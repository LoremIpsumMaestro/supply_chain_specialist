# rag-integration Specification

## Purpose
TBD - created by archiving change implement-mvp-features. Update Purpose after archive.
## Requirements
### Requirement: TypeSense Vector Database Setup
The system SHALL use TypeSense for hybrid (keyword + semantic) search with automatic 24h TTL for indexed documents.

#### Scenario: TypeSense collection created on startup
- **WHEN** the backend application starts
- **THEN** a TypeSense collection "document_chunks" is created if it doesn't exist
- **AND** the collection schema includes:
  - `chunk_id` (string, unique identifier)
  - `user_id` (string, facet for filtering)
  - `file_id` (string, facet for filtering)
  - `content` (string, searchable text)
  - `embedding` (float[], 1536 dimensions)
  - `metadata` (object, flexible JSON for citation data)
  - `document_expires_at` (int64, Unix timestamp for TTL)
- **AND** `document_expires_at` is set as default_sorting_field for TTL enforcement

#### Scenario: TypeSense TTL automatically purges expired chunks
- **WHEN** 24 hours have elapsed since chunk indexing
- **THEN** TypeSense automatically removes the chunk via native TTL
- **AND** the chunk is no longer returned in search results
- **AND** no manual cleanup job is required

#### Scenario: TypeSense connection failure
- **WHEN** the backend cannot connect to TypeSense on startup
- **THEN** an error is logged with connection details
- **AND** the application continues to run but RAG features are disabled
- **AND** file uploads still work but show "indexing unavailable" status

### Requirement: Embedding Generation
The system SHALL generate OpenAI embeddings for document chunks to enable semantic search.

#### Scenario: Generate embedding for single chunk
- **WHEN** a document chunk is ready for indexing
- **THEN** the chunk content is sent to OpenAI API (text-embedding-3-small)
- **AND** a 1536-dimensional embedding vector is returned
- **AND** the embedding is cached to avoid duplicate API calls

#### Scenario: Batch embedding generation
- **WHEN** multiple chunks (100+) need embedding simultaneously
- **THEN** chunks are batched in groups of 100 (OpenAI limit)
- **AND** each batch is sent in a single API call
- **AND** embeddings are returned in the same order as input chunks

#### Scenario: Embedding API rate limit exceeded
- **WHEN** the OpenAI embedding API returns 429 Too Many Requests
- **THEN** the request is retried with exponential backoff (3 attempts)
- **AND** if all retries fail, the chunk indexing fails gracefully
- **AND** the file processing_status is set to 'failed' with error message

#### Scenario: Embedding caching based on content hash
- **WHEN** the same text content is indexed multiple times
- **THEN** the embedding is retrieved from cache (Redis) instead of calling OpenAI API
- **AND** cache key is based on SHA256 hash of content
- **AND** cache TTL is 24 hours (aligned with document TTL)

### Requirement: Document Chunk Indexing
The system SHALL index parsed document chunks into TypeSense with embeddings and metadata.

#### Scenario: Index chunks after document processing
- **WHEN** document parsing completes successfully
- **THEN** for each chunk:
  - Generate embedding (or retrieve from cache)
  - Insert into TypeSense collection with:
    - `chunk_id`: UUID
    - `user_id`: file owner
    - `file_id`: source file ID
    - `content`: chunk text
    - `embedding`: vector
    - `metadata`: citation metadata (filename, sheet_name, cell_ref, page, etc.)
    - `document_expires_at`: now() + 86400 seconds
- **AND** the file processing_status is updated to 'completed'

#### Scenario: Index large file with 1000+ chunks
- **WHEN** a large file generates more than 1000 chunks
- **THEN** chunks are indexed in batches of 100
- **AND** indexing progresses until all chunks are inserted
- **AND** if one batch fails, remaining batches still attempt indexing

#### Scenario: TypeSense indexing fails
- **WHEN** TypeSense returns an error during chunk insertion
- **THEN** the error is logged with chunk_id and file_id
- **AND** the file processing_status remains 'processing' or is set to 'failed'
- **AND** the user sees an error message in UI

### Requirement: Hybrid Search
The system SHALL perform hybrid search combining keyword matching and semantic vector search.

#### Scenario: User query triggers hybrid search
- **WHEN** a user sends a chat message in a conversation with uploaded files
- **THEN** the query text is sent to RAG service for search
- **AND** the search uses both:
  - Keyword search on `content` field (BM25 ranking)
  - Semantic search on `embedding` field (cosine similarity)
- **AND** results are combined with weighted scoring (70% vector, 30% keyword)
- **AND** top 5 most relevant chunks are returned

#### Scenario: Search filtered by user_id for security
- **WHEN** a search is executed
- **THEN** results are filtered to only include chunks where user_id matches the requester
- **AND** no user can see chunks from another user's documents
- **AND** this implements Row Level Security (RLS) for RAG

#### Scenario: Search with no relevant results
- **WHEN** a user query has no semantically similar chunks in their documents
- **AND** no keyword matches exist
- **THEN** the search returns an empty result set
- **AND** the LLM is instructed to respond: "Je n'ai pas trouvé d'information pertinente dans vos documents concernant cette question."

#### Scenario: Search prioritizes recent documents
- **WHEN** multiple chunks have similar relevance scores
- **THEN** chunks from more recently uploaded files are ranked higher
- **AND** this is achieved by including created_at timestamp in scoring formula

### Requirement: RAG Context Injection
The LLM service SHALL inject RAG context AND system date into all prompts for anti-hallucination and temporal awareness.

**Changes from original**: Added system date injection requirement.

#### Scenario: System date injected in prompt
- **WHEN** the LLM builds a system prompt for any query
- **THEN** the prompt SHALL include the current date in French format before RAG context
- **AND** use format: "DATE ACTUELLE: DD Month YYYY" (example: "DATE ACTUELLE: 29 janvier 2026")

#### Scenario: Combined temporal and RAG context
- **WHEN** a user asks "Are any deliveries late?"
- **AND** RAG retrieves chunks with delivery dates
- **THEN** the system prompt SHALL include:
  1. Current system date
  2. RAG context with document excerpts and dates
  3. Instructions to calculate delays using the current date

#### Scenario: No RAG results but date still injected
- **WHEN** a user asks a general question with no relevant RAG results
- **THEN** the system SHALL still inject the current date in the prompt
- **AND** the LLM can answer using general knowledge with temporal awareness

#### Scenario: Temporal context in RAG results
- **WHEN** RAG search returns chunks with `temporal_context` in metadata
- **THEN** the system SHALL include temporal metrics in the RAG context string
- **AND** format example: "[Source 1: sales.xlsx, cellule C12, date: 15 déc 2025, tendance: +25% vs mois précédent]"

---

### Requirement: Citation Extraction and Display
Citations SHALL include temporal context metadata when available.

**Changes from original**: Extended to include temporal metadata in citations.

#### Scenario: Citation with temporal context
- **WHEN** a search result includes `temporal_context` in metadata
- **THEN** the citation SHALL display the date and temporal metrics
- **AND** format example: "Selon la cellule C12 (feuille 'Ventes', fichier sales.xlsx, date: 15 décembre 2025): 150 unités (+25% vs novembre)"

#### Scenario: Citation without temporal context
- **WHEN** a PDF chunk has no temporal metadata
- **THEN** the citation SHALL use the original format without temporal info
- **AND** format example: "Selon la page 3 du fichier rapport.pdf: ..."

### Requirement: RAG Query Performance
The system SHALL meet performance targets for search latency and response time.

#### Scenario: TypeSense search completes quickly
- **WHEN** a hybrid search query is executed
- **THEN** the TypeSense search completes in less than 50ms
- **AND** this latency is logged for monitoring

#### Scenario: RAG-enhanced chat response starts streaming quickly
- **WHEN** a user sends a chat message with RAG context
- **THEN** the first token of the LLM response arrives within 2 seconds
- **AND** this includes time for: search (50ms) + embedding generation (200ms) + LLM first token (1.5s)

#### Scenario: Large context does not degrade performance
- **WHEN** a query retrieves 5 chunks totaling 2000 tokens of context
- **THEN** the LLM response still starts streaming within 2 seconds
- **AND** context is truncated if it exceeds 3000 tokens (to fit prompt limits)

### Requirement: Multi-File Cross-Document Search
The system SHALL support queries across multiple uploaded files in a conversation.

#### Scenario: Query references data from two files
- **WHEN** a user asks "Compare les stocks entre production.xlsx et inventaire.csv"
- **THEN** the hybrid search retrieves chunks from both files
- **AND** the LLM response cites both sources
- **AND** citations indicate which file each piece of information came from

#### Scenario: File-specific query
- **WHEN** a user asks "What is in the rapport.pdf file?"
- **THEN** the search is filtered to only chunks where metadata.filename = "rapport.pdf"
- **AND** results only include chunks from that specific file

### Requirement: RAG Accuracy Validation
The system SHALL track RAG quality metrics to detect hallucinations or incorrect citations.

#### Scenario: Log citation accuracy
- **WHEN** a citation is generated by the LLM
- **THEN** the system verifies that the cited source exists in the search results
- **AND** if a citation references a non-existent source, a warning is logged

#### Scenario: Log "no information found" responses
- **WHEN** the LLM responds that no information was found
- **THEN** this is logged as a RAG miss
- **AND** metrics track the percentage of queries with no relevant chunks (target: < 20%)

#### Scenario: User feedback on citation accuracy
- **WHEN** a user sees a citation in the UI
- **THEN** a thumbs-up/down button allows feedback on accuracy
- **AND** negative feedback is logged for review and model tuning

