# rag-integration Specification

## Purpose
Provide Retrieval Augmented Generation (RAG) capabilities using TypeSense vector database and OpenAI embeddings to enable accurate, sourced responses from uploaded Supply Chain documents. Ensure anti-hallucination through strict citation requirements and low temperature LLM configuration.

## ADDED Requirements

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
The system SHALL inject retrieved chunks into LLM prompts with citation metadata.

#### Scenario: Relevant chunks included in LLM prompt
- **WHEN** hybrid search returns 5 relevant chunks for a user query
- **THEN** the chunks are formatted into a context string:
  ```
  Voici les informations pertinentes de vos documents:

  [Source 1: production.xlsx, feuille 'Stocks', cellule C12]
  Contenu: Quantité en stock: 150 unités

  [Source 2: rapport.pdf, page 3]
  Contenu: Le stock de sécurité recommandé est de 200 unités pour ce produit.
  ```
- **AND** this context is injected into the system prompt before the user query
- **AND** the LLM is instructed to always cite sources using the exact format provided

#### Scenario: LLM generates response with citations
- **WHEN** the LLM generates a response using RAG context
- **THEN** the response includes inline citations matching the source format
- **AND** citations are parsed from the response text
- **AND** citation metadata is extracted and stored in the message.citations field
- **AND** citations are displayed in the UI with the Citation component

#### Scenario: LLM temperature set for anti-hallucination
- **WHEN** a RAG-enabled chat request is processed
- **THEN** the LLM temperature is set to 0.1 (deterministic)
- **AND** the system prompt includes:
  - "Réponds UNIQUEMENT en te basant sur les sources fournies."
  - "Si l'information n'est pas dans les sources, dis clairement que tu ne l'as pas trouvée."
  - "N'invente JAMAIS d'informations."
- **AND** this prevents hallucinations

#### Scenario: No relevant chunks found
- **WHEN** hybrid search returns no results for a query
- **THEN** the LLM prompt includes no context (only user query)
- **AND** the system prompt instructs: "Aucune information pertinente n'a été trouvée dans les documents. Informe l'utilisateur que tu n'as pas de données sur ce sujet."
- **AND** the LLM responds accordingly without hallucinating

### Requirement: Citation Extraction and Display
The system SHALL extract citations from LLM responses and display them with rich metadata.

#### Scenario: Parse citations from LLM response
- **WHEN** the LLM response contains text like "Selon la cellule C12 (feuille 'Stocks' du fichier production.xlsx): 150"
- **THEN** a citation parser extracts:
  - Citation text: "Selon la cellule C12..."
  - Source metadata: {filename: "production.xlsx", sheet_name: "Stocks", cell_ref: "C12"}
- **AND** the citation is stored in message.citations as CitationMetadata

#### Scenario: Display Excel citation in UI
- **WHEN** a message contains an Excel citation
- **THEN** the citation is displayed as a Badge component
- **AND** the badge text shows: "📊 production.xlsx - Stocks!C12"
- **AND** hovering shows a tooltip with full metadata (filename, sheet, cell, value)

#### Scenario: Display PDF citation in UI
- **WHEN** a message contains a PDF citation
- **THEN** the citation is displayed as a Badge component
- **AND** the badge text shows: "📄 rapport.pdf - Page 3"
- **AND** hovering shows a tooltip with excerpt text

#### Scenario: Multiple citations in one message
- **WHEN** a message contains 3 citations from different sources
- **THEN** each citation is displayed as a separate badge
- **AND** badges are inline with the text at the relevant position

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
