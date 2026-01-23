# Implementation Tasks

## Overview
Séquence de tâches pour implémenter les 5 capabilities MVP. Les tâches sont ordonnées pour maximiser la valeur livrée incrémentalement et respecter les dépendances.

---

## Phase 1: RAG Pipeline (Semaine 1-2)

### Capability: file-upload

#### Task 1.1: Setup MinIO Storage Service
**Description**: Configurer MinIO dans Docker Compose et créer le service storage côté backend.

**Steps**:
1. Ajouter MinIO au docker-compose.yml (port 9000, console 9001)
2. Créer `backend/services/storage_service.py`:
   - `upload_file(file, user_id) -> file_id`
   - `download_file(file_id) -> bytes`
   - `delete_file(file_id) -> bool`
   - TTL via MinIO lifecycle policy (24h)
3. Ajouter minio SDK à requirements.txt
4. Configurer env vars (MINIO_ENDPOINT, ACCESS_KEY, SECRET_KEY)

**Validation**:
- MinIO accessible via console (localhost:9001)
- Upload/download via Python SDK fonctionne

**Estimated Effort**: 0.5 jour

---

#### Task 1.2: Create File Database Schema
**Description**: Ajouter table `files` pour tracker métadonnées des fichiers uploadés.

**Steps**:
1. Créer migration `003_create_files_table.sql`:
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
     expires_at TIMESTAMPTZ NOT NULL
   );
   CREATE INDEX idx_files_user_id ON files(user_id);
   CREATE INDEX idx_files_expires_at ON files(expires_at);
   ```
2. Créer modèle `backend/models/file.py` (Pydantic + SQLAlchemy)
3. Ajouter enum FileProcessingStatus (pending, processing, completed, failed)

**Validation**:
- Migration up/down fonctionne
- Model validation respecte contraintes

**Estimated Effort**: 0.5 jour

---

#### Task 1.3: Implement File Upload API
**Description**: Créer endpoint POST /api/files/upload avec validation stricte.

**Steps**:
1. Créer `backend/api/files.py` avec endpoint:
   - POST /api/files/upload (multipart/form-data)
   - Body: file (binary), conversation_id (optional)
   - Validation: type MIME (.xlsx, .csv, .pdf, .docx, .pptx, .txt), size (< 50MB)
   - Response: file metadata (id, filename, type, size)
2. Logique:
   - Valider type MIME et extension
   - Générer unique object key (user_id/file_id/filename)
   - Upload vers MinIO via storage_service
   - Insérer metadata dans PostgreSQL
   - Set expires_at = now() + 24h
3. Ajouter rate limiting (max 10 uploads/min par user)
4. Error handling (413 Payload Too Large, 415 Unsupported Media Type)

**Validation**:
- Upload de chaque format fonctionne
- Fichiers > 50MB rejetés avec 413
- Fichiers .exe rejetés avec 415

**Estimated Effort**: 1 jour

---

#### Task 1.4: Implement File Listing and Delete APIs
**Description**: Endpoints pour lister et supprimer fichiers.

**Steps**:
1. GET /api/files?conversation_id={id} - Lister fichiers d'une conversation
2. DELETE /api/files/{file_id} - Supprimer fichier (MinIO + PostgreSQL)
3. Vérifier ownership (user_id match)

**Validation**:
- Listing retourne tous fichiers user
- Delete supprime MinIO + DB

**Estimated Effort**: 0.5 jour

---

#### Task 1.5: Build File Upload UI Component
**Description**: Composant React avec drag & drop et file picker.

**Steps**:
1. Installer react-dropzone
2. Créer `frontend/components/chat/FileUpload.tsx`:
   - Drag & drop zone stylisée
   - File picker (clic sur zone)
   - Preview filename + size
   - Progress bar upload
   - Error display (taille, type)
3. Ajouter bouton upload dans MessageInput
4. Afficher fichiers uploadés dans conversation (badge avec nom)
5. Store: ajouter `fileStore.ts` (uploadFile, files list)

**Validation**:
- Drag & drop fonctionne
- Progress bar s'affiche
- Fichiers listés dans sidebar

**Estimated Effort**: 1 jour

**Parallelizable**: Peut se faire en // avec Task 1.3-1.4

---

### Capability: document-processing

#### Task 2.1: Implement Excel Parser
**Description**: Parser openpyxl pour extraction cellule par cellule.

**Steps**:
1. Créer `backend/services/document_parser.py` avec classe `ExcelParser`
2. Méthode `parse(file_path) -> List[DocumentChunk]`:
   - Itérer sur toutes les sheets
   - Pour chaque cellule non vide:
     - Extraire value, row, column, cell_ref (ex: "C12")
     - Créer DocumentChunk avec metadata:
       ```python
       {
         "filename": str,
         "file_type": "excel",
         "sheet_name": str,
         "cell_ref": str,  # "C12"
         "row": int,
         "column": int,
         "value": str
       }
       ```
3. Gérer formules Excel (display value, pas formule)
4. Gérer merged cells
5. Skip cellules vides

**Validation**:
- Fichier Excel test avec 3 sheets parsé correctement
- Cellules mergées gérées
- Metadata complète

**Estimated Effort**: 1.5 jour

---

#### Task 2.2: Implement PDF Parser
**Description**: Parser PyPDF2 pour extraction par page.

**Steps**:
1. Classe `PDFParser` dans document_parser.py
2. Méthode `parse(file_path) -> List[DocumentChunk]`:
   - Extraire texte page par page
   - Chunker si page > 1000 tokens (split par paragraphe)
   - Metadata:
     ```python
     {
       "filename": str,
       "file_type": "pdf",
       "page": int,
       "chunk_index": int  # si split
     }
     ```
3. Gérer PDFs corrompus (try/except)

**Validation**:
- PDF multi-pages parsé
- Pages longues chunkées

**Estimated Effort**: 1 jour

---

#### Task 2.3: Implement Word/PowerPoint/CSV/Text Parsers
**Description**: Parsers pour formats restants.

**Steps**:
1. **WordParser** (python-docx):
   - Extraction paragraphe par paragraphe
   - Metadata: filename, paragraph_index
2. **PowerPointParser** (python-pptx):
   - Extraction slide par slide (title + body text)
   - Metadata: filename, slide_number
3. **CSVParser** (pandas):
   - Ligne par ligne
   - Metadata: filename, row_number, column_headers
4. **TextParser**:
   - Split par lignes ou paragraphes (< 1000 tokens)
   - Metadata: filename, line_number

**Validation**:
- Chaque format parse correctement
- Metadata cohérente

**Estimated Effort**: 1.5 jour

**Parallelizable**: Peut se faire en // avec Task 2.2

---

#### Task 2.4: Create Document Processing Job
**Description**: Job asynchrone Celery pour trigger parsing après upload.

**Steps**:
1. Créer `backend/tasks/document_tasks.py` avec task:
   ```python
   @celery.app.task
   def process_document(file_id: str):
     # 1. Download file from MinIO
     # 2. Detect type and call appropriate parser
     # 3. Store chunks (next task handles indexing)
     # 4. Update file.processing_status = 'completed'
   ```
2. Trigger depuis POST /api/files/upload (après upload MinIO)
3. Error handling: set status='failed' si parser échoue

**Validation**:
- Upload déclenche job automatiquement
- Status updated correctement

**Estimated Effort**: 1 jour

---

### Capability: rag-integration

#### Task 3.1: Setup TypeSense Service
**Description**: Configurer TypeSense dans Docker Compose et créer collection.

**Steps**:
1. Ajouter TypeSense au docker-compose.yml (port 8108)
2. Créer `backend/services/rag_service.py` avec `TypeSenseService`
3. Méthode `create_collection()`:
   - Schema:
     ```json
     {
       "name": "document_chunks",
       "fields": [
         {"name": "chunk_id", "type": "string"},
         {"name": "user_id", "type": "string", "facet": true},
         {"name": "file_id", "type": "string", "facet": true},
         {"name": "content", "type": "string"},
         {"name": "embedding", "type": "float[]", "num_dim": 1536},
         {"name": "metadata", "type": "object"},
         {"name": "document_expires_at", "type": "int64"}
       ]
     }
     ```
   - Enable TTL: `default_sorting_field: "document_expires_at"`
4. Configurer env vars (TYPESENSE_API_KEY, TYPESENSE_HOST)

**Validation**:
- TypeSense accessible (localhost:8108)
- Collection créée avec bon schema

**Estimated Effort**: 0.5 jour

---

#### Task 3.2: Implement Embedding Generation
**Description**: Service pour générer embeddings OpenAI.

**Steps**:
1. Dans rag_service.py, ajouter méthode:
   ```python
   def generate_embedding(text: str) -> List[float]:
     # OpenAI API: text-embedding-3-small
     # Return 1536 dim vector
   ```
2. Batching: traiter 100 chunks à la fois (limite OpenAI)
3. Caching: vérifier si embedding existe déjà (hash content)
4. Error handling: retry 3x si API timeout

**Validation**:
- Embedding généré pour texte test
- Batching fonctionne

**Estimated Effort**: 1 jour

---

#### Task 3.3: Implement Document Indexing
**Description**: Indexer chunks parsés dans TypeSense après parsing.

**Steps**:
1. Modifier `backend/tasks/document_tasks.py` task:
   - Après parsing, pour chaque chunk:
     - Générer embedding
     - Insérer dans TypeSense collection
     - Set document_expires_at = now() + 86400s
2. Méthode dans rag_service.py:
   ```python
   def index_chunks(chunks: List[DocumentChunk], user_id: str, file_id: str):
     # Generate embeddings (batch)
     # Insert into TypeSense
   ```

**Validation**:
- Upload → Parsing → Indexing E2E fonctionne
- TypeSense contient chunks avec embeddings

**Estimated Effort**: 1 jour

---

#### Task 3.4: Implement Hybrid Search
**Description**: Recherche hybride (keyword + semantic) dans TypeSense.

**Steps**:
1. Méthode dans rag_service.py:
   ```python
   def search(query: str, user_id: str, top_k: int = 5) -> List[SearchResult]:
     # 1. Generate query embedding
     # 2. TypeSense hybrid search:
     #    - Vector search (embedding similarity)
     #    - Keyword search (content field)
     # 3. Combine results (weighted: 70% vector, 30% keyword)
     # 4. Filter by user_id (RLS)
     # 5. Return top_k results with metadata
   ```
2. Scorer: cosine similarity pour vector, BM25 pour keyword

**Validation**:
- Query "stocks négatifs" retourne chunks pertinents
- Metadata complète dans résultats

**Estimated Effort**: 1.5 jour

---

#### Task 3.5: Integrate RAG into LLM Service
**Description**: Injecter contexte RAG dans prompts LLM avec citations.

**Steps**:
1. Modifier `backend/services/llm_service.py`:
   - Avant génération réponse:
     - Call rag_service.search(user_query, user_id)
     - Construire context string:
       ```
       Voici les informations pertinentes des documents fournis:

       [Source 1: fichier.xlsx, feuille 'Stocks', cellule C12]
       Valeur: 150 unités

       [Source 2: rapport.pdf, page 3]
       Texte: "Le stock de sécurité recommandé est de 200 unités"
       ```
   - Injecter dans system prompt
   - Configurer temperature=0.1 (anti-hallucination)
2. Instructions prompt:
   - "Toujours citer les sources avec format exact"
   - "Si aucune source pertinente, dire 'Je n'ai pas trouvé d'information sur ce sujet dans vos documents'"
3. Parser réponse LLM pour extraire citations et les afficher dans UI

**Validation**:
- Question sur fichier retourne réponse avec citation
- Question hors sujet retourne "pas d'information"

**Estimated Effort**: 2 jours

---

#### Task 3.6: Update Message Model for Citations
**Description**: Ajouter champ citations au modèle Message.

**Steps**:
1. Migration `004_add_citations_to_messages.sql`:
   ```sql
   ALTER TABLE messages ADD COLUMN citations JSONB;
   ```
2. Modifier `backend/models/message.py`:
   - Ajouter `citations: List[CitationMetadata]`
3. Frontend: parser citations et afficher avec composant Citation.tsx

**Validation**:
- Citations sauvegardées en DB
- Affichées dans UI avec formatting correct

**Estimated Effort**: 0.5 jour

---

## Phase 2: Intelligence Métier + Sécurité (Semaine 3)

### Capability: alert-mode

#### Task 4.1: Implement Alert Detection Rules
**Description**: Service pour détecter incohérences métier Supply Chain.

**Steps**:
1. Créer `backend/services/alert_service.py` avec classe `SupplyChainAlertDetector`
2. Méthodes de détection:
   - `detect_negative_stock(chunks)`: chercher valeurs numériques < 0 dans colonnes "stock", "inventory", "quantity"
   - `detect_date_inconsistencies(chunks)`: parser dates et vérifier livraison >= commande
   - `detect_negative_quantities(chunks)`: quantités < 0 dans commandes/BL
   - `detect_outlier_lead_times(chunks)`: lead times > 90 jours (configurable)
3. Retourner `List[Alert]` avec:
   ```python
   {
     "type": "negative_stock",
     "severity": "critical",
     "message": "Stock négatif détecté: -50 unités",
     "source": CitationMetadata,
     "value": -50
   }
   ```

**Validation**:
- Fichier Excel test avec stock négatif détecté
- Dates incohérentes détectées

**Estimated Effort**: 2 jours

---

#### Task 4.2: Integrate Alerts into Document Processing
**Description**: Détecter alertes automatiquement après parsing.

**Steps**:
1. Modifier `backend/tasks/document_tasks.py`:
   - Après parsing, avant indexing:
     - Call alert_service.detect_all_alerts(chunks)
     - Sauvegarder alertes dans nouvelle table `alerts`
2. Créer migration `005_create_alerts_table.sql`
3. Model `backend/models/alert.py`

**Validation**:
- Upload fichier → Alertes détectées et sauvegardées

**Estimated Effort**: 1 jour

---

#### Task 4.3: Display Alerts in UI
**Description**: Afficher alertes dans l'interface chat.

**Steps**:
1. Créer composant `frontend/components/chat/AlertBadge.tsx`:
   - Badge rouge pour critical, orange pour warning
   - Tooltip avec détails
   - Icon (exclamation triangle)
2. Endpoint GET /api/files/{file_id}/alerts
3. Afficher alertes après upload dans MessageList

**Validation**:
- Alertes visibles dans UI après upload
- Severity correctly styled

**Estimated Effort**: 0.5 jour

**Parallelizable**: Peut se faire en // avec Task 4.2

---

### Capability: auth-system

#### Task 5.1: Create User Model and Auth Endpoints
**Description**: Modèle User et endpoints register/login/refresh.

**Steps**:
1. Migration `006_create_users_table.sql`:
   ```sql
   CREATE TABLE users (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     email VARCHAR(255) UNIQUE NOT NULL,
     hashed_password VARCHAR(255) NOT NULL,
     full_name VARCHAR(255),
     is_active BOOLEAN DEFAULT TRUE,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```
2. Model `backend/models/user.py`
3. Créer `backend/api/auth.py`:
   - POST /auth/register (email, password, full_name)
   - POST /auth/login (email, password) → access_token + refresh_token
   - POST /auth/refresh (refresh_token) → new access_token
4. Password hashing: passlib + bcrypt
5. JWT tokens: access 15min, refresh 7 jours

**Validation**:
- Register → Login → Access protected endpoint fonctionne
- Refresh token fonctionne

**Estimated Effort**: 2 jours

---

#### Task 5.2: Update Frontend with Auth Flow
**Description**: Login/register UI et token management.

**Steps**:
1. Créer pages:
   - `/login` avec LoginForm
   - `/register` avec RegisterForm
2. Store: `authStore.ts` (login, logout, refresh, user state)
3. Axios interceptor pour injecter token et refresh auto
4. Protected route wrapper
5. Logout button dans sidebar

**Validation**:
- Login → Chat → Logout fonctionne
- Token refresh automatique avant expiry

**Estimated Effort**: 1.5 jour

**Parallelizable**: Peut se faire en // avec Task 5.1

---

## Testing & Finalization

#### Task 6.1: Write Unit Tests
**Description**: Tests unitaires backend critiques.

**Steps**:
1. Tests parsers (pytest):
   - ExcelParser: 5 tests (sheets, formules, merged cells)
   - PDFParser: 3 tests
   - WordParser: 2 tests
2. Tests RAG service:
   - Embedding generation
   - Hybrid search
3. Tests alert detection:
   - Chaque règle (negative stock, dates, etc.)
4. Coverage minimum: 80%

**Estimated Effort**: 2 jours

---

#### Task 6.2: E2E Tests with Playwright
**Description**: Tests E2E des flows critiques.

**Steps**:
1. Setup Playwright (déjà mentionné dans CLAUDE.md)
2. Tests:
   - Upload fichier Excel → Question → Citation affichée
   - Upload fichier avec stock négatif → Alerte affichée
   - Login → Upload → Logout
3. Tests responsive (mobile/tablet/desktop)

**Validation**:
- Tous tests E2E passent
- Responsive vérifié

**Estimated Effort**: 2 jours

---

#### Task 6.3: Update Documentation
**Description**: Mettre à jour README avec nouvelles fonctionnalités.

**Steps**:
1. Documenter upload flow
2. Documenter formats supportés
3. Documenter alertes Supply Chain
4. Screenshots UI
5. Mettre à jour QUICKSTART.md

**Estimated Effort**: 0.5 jour

---

## Summary

**Total Estimated Effort**: ~23 jours
- Phase 1 (RAG Pipeline): 14 jours
- Phase 2 (Alertes + Auth): 5 jours
- Testing & Docs: 4 jours

**Parallelization Opportunities**:
- Task 1.5 // Task 1.3-1.4
- Task 2.3 // Task 2.2
- Task 4.3 // Task 4.2
- Task 5.2 // Task 5.1

**Critical Path**:
1.1 → 1.2 → 1.3 → 1.4 → 2.1 → 2.4 → 3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6

**Key Dependencies**:
- `document-processing` dépend de `file-upload` (Task 2.x dépend de Task 1.x)
- `rag-integration` dépend de `document-processing` (Task 3.x dépend de Task 2.x)
- `alert-mode` dépend de `document-processing` (Task 4.x dépend de Task 2.x)
- `auth-system` est indépendant (peut se faire en parallèle)
