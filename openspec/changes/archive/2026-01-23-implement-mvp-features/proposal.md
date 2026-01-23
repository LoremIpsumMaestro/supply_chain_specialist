# Proposal: Implement MVP Core Features

## Problem Statement

L'interface de chat est implémentée (conversations, messages, streaming), mais les fonctionnalités métier critiques du MVP manquent:

1. **Upload & Traitement de Documents**: Pas de système d'upload fonctionnel ni de parsing des formats (Excel, PDF, Word, PowerPoint, CSV, Texte)
2. **RAG & Citations**: Pas d'indexation vectorielle ni de système de citations avec sources précises
3. **Mode Alerte**: Pas de détection d'incohérences métier Supply Chain
4. **Purge 24h**: Système de purge uniquement au niveau base de données, pas pour les fichiers et index vectoriels
5. **Authentification**: JWT configuré mais pas d'endpoints de login/register

Ces fonctionnalités sont **critiques** pour le MVP selon PRD.md Phase 1.

## Proposed Solution

Développer 5 capabilities indépendantes mais complémentaires:

### 1. **file-upload** (Priorité: HAUTE)
Système complet d'upload multi-formats avec validation, stockage temporaire MinIO, et métadonnées PostgreSQL.

**Scope**:
- Endpoints backend upload/download/delete
- Validation type MIME, taille (50MB max)
- Stockage MinIO avec TTL 24h
- UI composant d'upload (drag & drop, file picker)
- Support formats: .xlsx, .csv, .pdf, .docx, .pptx, .txt

### 2. **document-processing** (Priorité: HAUTE)
Parsers pour extraire texte structuré avec métadonnées précises (cellules Excel, pages PDF, etc.).

**Scope**:
- Parser Excel (openpyxl): extraction cellule par cellule avec sheet_name, cell_ref, row, column
- Parser PDF (PyPDF2): extraction par page
- Parser Word (python-docx): extraction par paragraphe
- Parser PowerPoint (python-pptx): extraction par slide
- Parser CSV/Texte: ligne par ligne
- Chunking intelligent pour RAG (< 1000 tokens/chunk)

**Relation**: Dépend de `file-upload` (nécessite fichiers uploadés).

### 3. **rag-integration** (Priorité: HAUTE)
Indexation vectorielle TypeSense + embeddings OpenAI pour recherche hybride (keyword + semantic) avec citations précises.

**Scope**:
- Collection TypeSense avec TTL 86400s
- Schema avec metadata enrichie (filename, sheet_name, cell_ref, page, slide, etc.)
- Embedding generation (text-embedding-3-small)
- Hybrid search (keyword + vector)
- Citation extraction avec formatage métier ("Selon la cellule C12...")
- Injection contexte RAG dans prompts LLM

**Relation**: Dépend de `document-processing` (nécessite chunks structurés).

### 4. **alert-mode** (Priorité: MOYENNE)
Détection d'incohérences métier Supply Chain dans les documents analysés.

**Scope**:
- Règles de détection:
  - Stocks négatifs
  - Dates incohérentes (livraison avant commande)
  - Quantités négatives
  - Lead times anormalement longs/courts (outliers)
- Alertes affichées dans le chat avec badge visuel
- Logs des alertes pour monitoring

**Relation**: Dépend de `document-processing` (analyse les données parsées).

### 5. **auth-system** (Priorité: MOYENNE)
Endpoints d'authentification complets pour remplacer le JWT mock actuel.

**Scope**:
- Modèle User (PostgreSQL)
- Endpoints: POST /auth/register, POST /auth/login, POST /auth/refresh
- Password hashing (passlib + bcrypt)
- JWT access tokens (15min) + refresh tokens (7 jours)
- Rate limiting login (5 tentatives/min)

**Relation**: Indépendant mais requis pour production.

## Scope & Sequencing

### Phase 1 (Semaine 1-2): RAG Pipeline Complet
1. **file-upload** (3 jours) → Tests
2. **document-processing** (4 jours) → Tests
3. **rag-integration** (5 jours) → Tests E2E RAG

**Livrable**: Upload de fichier → Parsing → Indexation → Questions avec citations précises fonctionnelles.

### Phase 2 (Semaine 3): Intelligence Métier + Sécurité
4. **alert-mode** (3 jours) → Tests
5. **auth-system** (2 jours) → Tests

**Livrable**: MVP complet avec détection d'incohérences et authentification sécurisée.

## Success Criteria

- [ ] Un utilisateur peut uploader un fichier Excel et poser une question sur une cellule précise
- [ ] Les citations affichent "Selon la cellule C12 (feuille 'Stocks' du fichier production.xlsx): valeur"
- [ ] Les stocks négatifs sont détectés et affichés avec un badge d'alerte
- [ ] La température LLM est configurée à 0.1 (anti-hallucination)
- [ ] Les fichiers et index sont purgés automatiquement après 24h
- [ ] L'authentification fonctionne avec register/login/refresh
- [ ] Tests couvrent 80%+ du code critique (parsers, RAG, alertes)

## Open Questions

1. **Embeddings**: OpenAI text-embedding-3-small (1536 dim) ou alternative (Cohere, HuggingFace) ?
   - **Recommandation**: OpenAI pour simplicité MVP, alternative en V1 si coûts élevés

2. **Chunking Strategy**: Chunk size optimal pour Excel (cellule par cellule) vs documents textuels (paragraphes) ?
   - **Recommandation**: Granularité maximale (cellule Excel), 500 tokens pour PDF/Word

3. **Alert Thresholds**: Seuils pour lead times "anormalement longs" (>60 jours? >90 jours?) ?
   - **Besoin de clarification utilisateur métier**

4. **MinIO vs S3**: MinIO local (Docker) pour MVP ou directement S3 compatible production ?
   - **Recommandation**: MinIO local MVP, migration S3 lors déploiement

5. **TypeSense TTL**: TTL natif (document_expires_at) ou cleanup manuel via Celery ?
   - **Recommandation**: TTL natif TypeSense (plus fiable)

## Dependencies

### External
- TypeSense v27.0+ (Docker)
- MinIO (Docker ou AWS S3)
- OpenAI API (embeddings + GPT-4)
- Python libs: openpyxl, PyPDF2, python-docx, python-pptx, pandas, langchain, typesense

### Internal
- Chat interface existante (`chat-interface` spec)
- Database schema (conversations, messages)
- LLM service (streaming)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| TypeSense TTL ne fonctionne pas correctement | HAUT | Tests E2E de purge + fallback Celery Beat |
| Parsing Excel échoue sur formats complexes | MOYEN | Validation stricte upload + error handling gracieux |
| Coûts embeddings OpenAI élevés | MOYEN | Caching embeddings + batch processing |
| Détection alertes avec faux positifs | FAIBLE | Thresholds conservateurs + logs pour tuning |

## Architectural Impact

- **Nouveau module**: `backend/services/document_parser.py` (parsers centralisés)
- **Nouveau module**: `backend/services/rag_service.py` (TypeSense + embeddings)
- **Nouveau module**: `backend/services/alert_service.py` (règles métier)
- **Nouveau module**: `backend/services/storage_service.py` (MinIO)
- **Nouveau endpoint**: `POST /api/files/upload`
- **Nouveau endpoint**: `POST /auth/register`, `POST /auth/login`
- **Frontend composant**: `FileUpload.tsx`, `AlertBadge.tsx`

Pas de changements breaking sur l'architecture existante.

## Related Changes

- Cette proposition doit être suivie par des propositions V1 (Phase 2 PRD):
  - `implement-temporal-intelligence` (injection date système, analyse saisonnalité)
  - `implement-dual-persona` (Mode Opérationnel vs Directeur)
  - `implement-export-reports` (Word/PDF/CSV exports)
