# Design Document: MVP Core Features Implementation

## Architectural Overview

This change introduces the core RAG (Retrieval Augmented Generation) pipeline and supporting features required for the MVP, building on the existing chat interface.

### High-Level Architecture

```
┌─────────────┐
│   Frontend  │ (Next.js + React)
│   (Upload   │
│    UI)      │
└──────┬──────┘
       │ POST /api/files/upload
       ▼
┌─────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                     │
│                                                          │
│  ┌──────────┐   ┌───────────┐   ┌──────────┐          │
│  │  Upload  │──▶│  Storage  │──▶│  Celery  │          │
│  │   API    │   │  (MinIO)  │   │   Task   │          │
│  └──────────┘   └───────────┘   └────┬─────┘          │
│                                       │                 │
│                                       ▼                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │        Document Processing Pipeline             │  │
│  │                                                  │  │
│  │  1. Parser (Excel/PDF/Word/PPT/CSV/Text)       │  │
│  │  2. Chunking (with metadata)                   │  │
│  │  3. Alert Detection (parallel)                 │  │
│  │  4. Embedding Generation (OpenAI)              │  │
│  │  5. TypeSense Indexing (with TTL)              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────┐   ┌───────────┐   ┌──────────┐          │
│  │   Chat   │──▶│    RAG    │──▶│   LLM    │          │
│  │   API    │   │  Service  │   │ Service  │          │
│  └──────────┘   └───────────┘   └──────────┘          │
│       │              │                │                 │
└───────┼──────────────┼────────────────┼─────────────────┘
        │              │                │
        ▼              ▼                ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │PostgreSQL│   │TypeSense │   │ OpenAI   │
  │(metadata)│   │(vectors) │   │   API    │
  └──────────┘   └──────────┘   └──────────┘
```

---

## Design Decisions

### 1. Storage: MinIO vs S3

**Decision**: Use MinIO for MVP, plan S3 migration for production.

**Rationale**:
- **MinIO Pros**:
  - Docker-compatible (easy local dev)
  - S3-compatible API (migration path)
  - Native TTL via lifecycle policies
  - No external dependencies or costs in dev
- **S3 Pros**:
  - Managed service (less ops overhead)
  - Better durability guarantees
  - Native integration with AWS ecosystem
- **Conclusion**: MinIO for MVP simplicity, migrate to S3 at production deployment.

**Trade-offs**:
- MinIO requires managing Docker container, but acceptable for MVP scale (<20 concurrent users).
- S3 migration later will be straightforward due to API compatibility.

---

### 2. Embeddings: Ollama vs Cloud APIs

**Decision**: Use Ollama with nomic-embed-text for MVP.

**Rationale**:
- **Ollama Pros**:
  - Self-hosted (no API costs, free)
  - Full control over data (confidentialité)
  - Fast local inference (< 100ms per batch)
  - Works offline
  - nomic-embed-text: 768 dimensions, optimized for RAG
- **OpenAI Pros** (rejected):
  - 1536 dimensions (marginal quality improvement)
  - Costs ~$20/month for MVP scale
  - Requires API keys
- **Conclusion**: Ollama aligns with project confidentiality requirements (no data sent to external APIs) and is free.

**Model Selection**:
- **Embeddings**: `nomic-embed-text` (768 dimensions, 8K context)
- **LLM**: `mistral:7b-instruct` (good French support, 8K context)

**Cost Estimate**:
- Ollama: $0/month (self-hosted)
- Hardware requirements: 8GB RAM minimum (fits MVP scale)

**Caching Strategy**:
- Cache embeddings in Redis with SHA256(content) as key
- 24h TTL aligned with document TTL
- Reduces redundant embedding generation

---

### 3. Vector Database: TypeSense vs Alternatives

**Decision**: Use TypeSense for hybrid search.

**Rationale**:
- **TypeSense Pros**:
  - Native hybrid search (keyword + vector)
  - Native TTL support (critical for 24h purge)
  - Fast (<50ms search latency)
  - Docker-compatible
  - Simpler than Pinecone/Weaviate for MVP
- **Pinecone Pros**:
  - Managed service
  - Better for very large scale (>1M vectors)
- **Weaviate Pros**:
  - More advanced querying
  - GraphQL API
- **Conclusion**: TypeSense best fit for MVP requirements (hybrid search + TTL + simplicity).

**Schema Design**:
```json
{
  "fields": [
    {"name": "chunk_id", "type": "string"},
    {"name": "user_id", "type": "string", "facet": true},  // RLS filtering
    {"name": "file_id", "type": "string", "facet": true},  // File filtering
    {"name": "content", "type": "string"},                 // Keyword search
    {"name": "embedding", "type": "float[]", "num_dim": 768}, // Vector search (Ollama nomic-embed-text)
    {"name": "metadata", "type": "object"},                // Citation data
    {"name": "document_expires_at", "type": "int64"}       // TTL
  ]
}
```

**Hybrid Search Scoring**:
- 70% vector similarity (cosine)
- 30% keyword relevance (BM25)
- Rationale: Favor semantic understanding but allow exact term matching for technical jargon.

---

### 4. Document Parsing: Granularity Strategy

**Decision**: Maximum granularity for Excel (cell-by-cell), semantic boundaries for text documents.

**Rationale**:
- **Excel**: Cell-level granularity enables precise citations ("cellule C12").
  - Trade-off: More chunks = more storage + embeddings cost, but essential for MVP requirement.
- **PDF/Word**: Paragraph-level chunking (< 1000 tokens).
  - Trade-off: Less precise citations but better context per chunk.
- **CSV**: Row-level chunking with column headers included.
- **PowerPoint**: Slide-level (title + body combined).

**Chunking Limits**:
- Max 1000 tokens per chunk (fits LLM context efficiently)
- Preserve semantic boundaries (paragraphs, sentences)
- Never split mid-sentence

---

### 5. Alert Detection: Rule-Based vs ML

**Decision**: Rule-based detection for MVP, ML for V2.

**Rationale**:
- **Rule-Based Pros**:
  - Deterministic and explainable
  - No training data required
  - Fast implementation
  - Low false positive rate (tunable thresholds)
- **ML-Based Pros**:
  - Can detect complex patterns
  - Adapts to user data
- **Conclusion**: Rule-based sufficient for MVP requirements (negative stocks, date inconsistencies, lead time outliers). ML anomaly detection can be added in V2 for advanced patterns.

**Alert Rules**:
1. **Negative Stock**: value < 0 in columns matching ["stock", "inventory", "quantity", "qty", "quantité"]
2. **Date Inconsistency**: delivery_date < order_date
3. **Negative Quantity**: order qty < 0
4. **Lead Time Outlier**: (delivery_date - order_date) > 90 days OR < 1 day

**Thresholds**:
- Configurable via environment variables
- Default to conservative values (minimize false positives)

---

### 6. Authentication: JWT vs Session

**Decision**: JWT tokens (access + refresh) for MVP.

**Rationale**:
- **JWT Pros**:
  - Stateless (no server-side session storage required)
  - Scalable (no session replication needed)
  - Standard for REST APIs
- **Session Pros**:
  - Can revoke sessions immediately (blacklist requires Redis overhead)
- **Conclusion**: JWT for MVP simplicity, add token blacklist in V1 if needed.

**Token Strategy**:
- **Access Token**: 15 min expiry (short-lived for security)
- **Refresh Token**: 7 days expiry (user convenience)
- **No Rotation**: Refresh tokens are not rotated on use in MVP (simplicity). Token rotation planned for V1.

---

### 7. Async Processing: Celery vs Alternatives

**Decision**: Use Celery with Redis broker for document processing.

**Rationale**:
- **Celery Pros**:
  - Mature, battle-tested
  - Retry logic built-in
  - Redis integration
- **FastAPI BackgroundTasks Pros**:
  - Simpler (no external service)
  - Good for lightweight tasks
- **Conclusion**: Celery required because document processing can take 10+ seconds for large files. BackgroundTasks would block the API response.

**Task Flow**:
1. Upload API enqueues task: `process_document(file_id)`
2. Celery worker:
   - Downloads file from MinIO
   - Parses with appropriate parser
   - Detects alerts (parallel)
   - Generates embeddings (batched)
   - Indexes in TypeSense
3. Updates `files.processing_status` to 'completed' or 'failed'

**Retry Policy**:
- Max 3 retries
- Exponential backoff: 5s, 25s, 125s
- Retry on transient errors (network, MinIO timeout)
- No retry on parser errors (corrupted file)

---

### 8. RAG Context Injection: Prompt Engineering

**Decision**: Inject RAG context in structured format with explicit citation instructions.

**System Prompt Template**:
```
Tu es un assistant IA spécialisé en Supply Chain. Réponds UNIQUEMENT en te basant sur les sources fournies ci-dessous.

SOURCES:
{retrieved_chunks}

RÈGLES:
1. Cite TOUJOURS tes sources avec le format exact fourni (fichier, feuille, cellule/page).
2. Si l'information n'est pas dans les sources, dis clairement: "Je n'ai pas trouvé d'information sur ce sujet dans vos documents."
3. N'invente JAMAIS d'informations.
4. Privilégie les réponses concises et précises.

QUESTION DE L'UTILISATEUR:
{user_query}
```

**Citation Format Examples**:
- Excel: "Selon la cellule C12 (feuille 'Stocks' du fichier production.xlsx): 150 unités"
- PDF: "D'après la page 3 du fichier rapport.pdf: ..."
- CSV: "Selon la ligne 15 du fichier stocks.csv (colonne 'Quantité'): ..."

**Temperature**:
- Set to 0.1 (deterministic, anti-hallucination)
- V1 can explore 0.3 for more conversational responses while maintaining source grounding

---

### 9. 24h Purge: Implementation Strategy

**Decision**: Native TTL features + pg_cron for database cleanup.

**Purge Mechanisms**:
1. **MinIO**: Lifecycle policy (S3-compatible) deletes objects after 24h
2. **TypeSense**: `document_expires_at` field with native TTL enforcement
3. **PostgreSQL**: pg_cron job runs daily to delete expired conversations, messages, files, alerts

**Why Not Celery Beat for Purge?**
- Native TTL is more reliable (no task queue failures)
- Celery Beat adds complexity (another service to monitor)
- pg_cron is simpler for database cleanup

**pg_cron Job**:
```sql
-- Runs daily at 2am
SELECT cron.schedule('purge_expired_data', '0 2 * * *', $$
  DELETE FROM conversations WHERE expires_at < NOW();
  DELETE FROM files WHERE expires_at < NOW();
  DELETE FROM alerts WHERE file_id NOT IN (SELECT id FROM files);
$$);
```

---

### 10. Frontend State Management: Zustand Stores

**Decision**: Extend existing Zustand stores for new features.

**New Stores**:
- `fileStore.ts`: Upload state, file list, processing status
- `alertStore.ts`: Alert list, filter by severity, mark as read

**Existing Stores** (extended):
- `conversationStore.ts`: Add file associations
- `messageStore.ts`: Add citation parsing logic

**Rationale**:
- Zustand already used for chat state (consistency)
- Lightweight, no boilerplate
- Good TypeScript support

---

## Data Models

### New Tables

#### files
```sql
CREATE TABLE files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL,
  file_type VARCHAR(50) NOT NULL,
  file_size_bytes INTEGER NOT NULL,
  minio_object_key VARCHAR(500) NOT NULL,
  processing_status VARCHAR(50) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  INDEX idx_files_user_id (user_id),
  INDEX idx_files_expires_at (expires_at)
);
```

#### alerts
```sql
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL,
  file_id UUID REFERENCES files(id) ON DELETE CASCADE,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  alert_type VARCHAR(50) NOT NULL,
  severity VARCHAR(20) NOT NULL,
  message TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  INDEX idx_alerts_file_id (file_id),
  INDEX idx_alerts_severity (severity)
);
```

#### users (for auth-system)
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  INDEX idx_users_email (email)
);
```

---

## API Design

### New Endpoints

#### Files
- `POST /api/files/upload` - Upload file (multipart/form-data)
- `GET /api/files` - List user's files
- `GET /api/files?conversation_id={id}` - List conversation files
- `DELETE /api/files/{file_id}` - Delete file

#### Alerts
- `GET /api/files/{file_id}/alerts` - List alerts for file
- `GET /api/conversations/{id}/alerts` - List alerts for conversation

#### Auth
- `POST /auth/register` - Create account
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token

---

## Performance Considerations

### Expected Latency

| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| File upload (10MB) | < 3s | Network + MinIO |
| Document parsing (Excel, 1000 rows) | < 5s | Celery async |
| Embedding generation (100 chunks) | < 2s | OpenAI batch API |
| TypeSense indexing (100 chunks) | < 500ms | Batched insert |
| TypeSense search | < 50ms | Hybrid search |
| RAG-enhanced chat response | < 2s | Search + LLM first token |

### Scaling Limits (MVP)

- **Concurrent users**: 10-20 (single backend instance)
- **File uploads/day**: ~500 (assuming avg 5 files/user/day × 100 users)
- **TypeSense chunks**: ~50k active (500 files × 100 chunks, 24h TTL)
- **Storage**: ~5GB active data (500 files × 10MB avg, 24h TTL)

### Bottlenecks & Mitigation

1. **OpenAI API rate limits**:
   - Mitigation: Embedding caching, batch processing
2. **TypeSense memory usage**:
   - Mitigation: 24h TTL keeps dataset small
3. **Celery task queue backlog**:
   - Mitigation: Monitor queue depth, add workers if needed

---

## Security Considerations

### Data Isolation

- **RLS (Row Level Security)**: All queries filter by `user_id`
- **TypeSense**: Facet filter by `user_id` in all searches
- **MinIO**: Object keys include `user_id` prefix for isolation

### Secrets Management

- All secrets in environment variables (`.env.local`)
- Never expose API keys to frontend
- JWT secret key rotated in production

### Input Validation

- File upload: MIME type + extension check
- File size limit: 50MB (configurable)
- Password: Complexity validation + bcrypt hashing
- SQL injection: SQLAlchemy ORM (parameterized queries)

---

## Testing Strategy

### Unit Tests (pytest)

- **Parsers**: Test each format with sample files (5 tests/parser)
- **Alert Detection**: Test each rule with edge cases
- **RAG Service**: Test embedding, search, citation extraction
- **Auth**: Test registration, login, token validation

### Integration Tests

- **Upload → Parse → Index**: E2E RAG pipeline
- **Chat → RAG → Citation**: Full query flow
- **Purge**: Verify TTL deletion after 24h (accelerated test)

### E2E Tests (Playwright)

- **Upload Excel → Ask Question → See Citation**: Critical path
- **Upload with Alert → See Alert Badge**: Alert flow
- **Login → Upload → Logout**: Auth flow

---

## Deployment Considerations

### Docker Compose (MVP)

All services in one compose file:
- Backend (FastAPI)
- Frontend (Next.js)
- PostgreSQL
- Redis
- MinIO
- TypeSense
- Celery worker

### Production (V1)

- Backend: Fly.io / Railway (2 instances, load balanced)
- Frontend: Vercel
- Database: Managed PostgreSQL (AWS RDS / DigitalOcean)
- Redis: Managed Redis (AWS ElastiCache / DigitalOcean)
- MinIO → AWS S3 migration
- TypeSense: Self-hosted on VPS or TypeSense Cloud

---

## Open Questions (Require User Input)

1. **Lead Time Thresholds**: What is considered "abnormally long" for your supply chain? (Default: 90 days)
2. **Alert Severity**: Should certain alert types be email-notified immediately? (MVP: UI only)
3. **File Retention**: Is 24h TTL strict requirement or can it be configurable per user? (MVP: 24h fixed)
4. **Multi-tenancy**: Will this be multi-org or single-org? (MVP: single-org, users isolated by user_id)

---

## Migration Path

### From Current State (Chat Interface Only)

1. Add MinIO, TypeSense to docker-compose
2. Run database migrations (003-006)
3. Deploy file upload UI components
4. Deploy Celery worker
5. Test upload → parse → index → query flow
6. Deploy alert detection
7. Deploy auth endpoints
8. Update frontend for auth flow

### Risk: Breaking Changes

- None expected - all new features are additive
- Existing chat functionality unchanged
- New endpoints are opt-in

---

## Success Metrics

### MVP Definition of Done

- [ ] User can upload Excel file and ask "What is in cell C12?" → Gets answer with citation
- [ ] User can upload file with negative stock → Sees alert badge
- [ ] Files auto-delete after 24h
- [ ] Temperature = 0.1, no hallucinations observed in test queries
- [ ] Auth flow (register → login → chat → logout) works
- [ ] All E2E Playwright tests pass

### Performance Targets

- [ ] TypeSense search < 50ms (p95)
- [ ] RAG-enhanced response < 2s first token (p95)
- [ ] File processing < 10s for 1000-row Excel (p95)

### Quality Targets

- [ ] Unit test coverage > 80% for critical code (parsers, RAG, alerts)
- [ ] Zero high-severity security issues (dependency scan)
- [ ] Documentation updated (README, API docs)
