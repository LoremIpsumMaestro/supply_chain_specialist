# Project Context

## Purpose
Assistant IA spécialisé Supply Chain avec interface de chat type "ChatGPT" pour professionnels (Opérationnels et Directeurs). L'outil permet d'interagir avec des LLM pour analyser des contextes opérationnels et stratégiques à partir de documents fournis par l'utilisateur.

**Objectifs clés:**
- Analyser des documents Supply Chain (Excel, PDF, Word, PowerPoint, CSV) avec citations précises
- Fournir une expertise métier avec prise en compte de la temporalité et saisonnalité
- Garantir une confidentialité stricte avec purge automatique des données après 24h
- Éviter les hallucinations via RAG (Retrieval Augmented Generation) ancré sur documents utilisateurs

**Roadmap:**
- **Phase MVP:** Interface chat, RAG de base, support multi-formats, citations systématiques, mode alerte
- **Phase V1:** Intelligence temporelle, double persona (Opérationnel/Directeur), exports structurés, comparaison de scénarios
- **Phase V2:** Simulateur What-if, analyse multi-documents complexe, bibliothèque de frameworks Supply Chain

## Tech Stack

### Frontend
- **Framework:** Next.js 15 + React 19
- **Styling:** TailwindCSS + shadcn/ui
- **Chat UI:** @vercel/ai (streaming support)
- **Upload:** react-dropzone
- **State Management:** Zustand
- **Forms:** React Hook Form + Zod validation
- **Language:** TypeScript

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **API:** REST + WebSocket streaming
- **Validation:** Pydantic v2
- **Authentication:** JWT (python-jose + passlib)

### RAG & LLM
- **LLM Providers:** OpenAI API / Anthropic Claude API
- **RAG Framework:** LangChain (Python)
- **Vector Database:** TypeSense (self-hosted) - Hybrid keyword + vector search
- **Embeddings:** OpenAI Embeddings (1536 dimensions)

### Document Processing
- **Excel:** openpyxl + pandas (accès cellule précis)
- **PDF:** PyPDF2
- **Word:** python-docx
- **PowerPoint:** python-pptx
- **Export:** reportlab (PDF) + python-docx (Word) + jinja2 (templates)

### Storage & Cache
- **Database:** PostgreSQL (conversations + metadata)
- **Cache/Queue:** Redis (TTL + Celery broker)
- **File Storage:** MinIO/S3-compatible (temporaire 24h)
- **TTL Management:** TypeSense natif (86400s) + pg_cron backup

### Job Scheduling
- **Task Queue:** Celery + Redis
- **Use Cases:** Génération rapports async, monitoring santé système
- **Note:** Purge 24h gérée nativement par TypeSense TTL (pas besoin de Celery Beat pour purge)

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Deployment:** Fly.io / Railway (backend) + Vercel (frontend)
- **Monitoring:** À définir (Phase V1)

## Project Conventions

### Code Style
- **Python:**
  - PEP 8 compliant (black formatter)
  - Type hints obligatoires (mypy strict mode)
  - Docstrings: Google style
  - Max line length: 100 caractères
  - Naming: snake_case (functions/variables), PascalCase (classes)

- **TypeScript:**
  - ESLint + Prettier
  - Strict mode enabled
  - Naming: camelCase (functions/variables), PascalCase (components/classes)
  - React: Functional components + hooks only

### Architecture Patterns
- **Separation of Concerns:**
  - Frontend: Pure UI layer, no business logic
  - Backend: 3-layer architecture (API routes → Services → Data Access)
  - RAG Engine: Isolated module (indexing, retrieval, citations)

- **RAG Pipeline:**
  1. Document Upload → Parsing → Chunking
  2. Embedding Generation → TypeSense Indexing (with TTL + rich metadata)
  3. Query → Hybrid Search (keyword + vector) → Citation Extraction
  4. LLM Context Building → Streaming Response

- **Citation System:**
  - Toujours inclure source exacte (fichier, feuille, cellule pour Excel)
  - Métadonnées TypeSense: `filename`, `sheet_name`, `cell_ref`, `row`, `column`
  - Format: "Selon la cellule C12 (feuille 'Stocks' du fichier production.xlsx): ..."

- **Security:**
  - Row Level Security pour isolation utilisateurs
  - JWT tokens avec refresh mechanism
  - Rate limiting sur API endpoints
  - Validation stricte des uploads (type MIME, taille max)

### Testing Strategy
- **Python Backend:**
  - Unit tests: pytest
  - Coverage minimum: 80%
  - Test des parsers de documents (critiques)
  - Test des citations Excel (précision requise)
  - Test de purge TTL TypeSense

- **Frontend:**
  - Component tests: Jest + React Testing Library
  - E2E: Playwright (Phase V1)
  - Test streaming chat UI
  - Test upload multi-fichiers

- **RAG Quality:**
  - Tests anti-hallucination (température 0.1)
  - Validation citations précises
  - Test détection d'incohérences (stocks négatifs, dates invalides)

### Git Workflow
- **Branching:** GitFlow
  - `main`: Production-ready
  - `develop`: Integration branch
  - `feature/*`: Nouvelles fonctionnalités
  - `hotfix/*`: Corrections urgentes

- **Commits:** Conventional Commits
  - `feat:` Nouvelle fonctionnalité
  - `fix:` Correction de bug
  - `docs:` Documentation
  - `refactor:` Refactoring sans changement de comportement
  - `test:` Ajout/modification tests
  - `chore:` Maintenance (deps, config)

- **PR Requirements:**
  - Tests passants
  - Code review obligatoire
  - Documentation à jour si nécessaire

## Domain Context

### Supply Chain Terminology
- **Rupture de stock:** Out of stock situation (critical alert)
- **Lead Time:** Délai de livraison fournisseur
- **BFR (Besoin en Fonds de Roulement):** Working capital requirement
- **Point de commande:** Reorder point
- **Stock de sécurité:** Safety stock
- **Saisonnalité:** Seasonal patterns in demand/supply

### Business Logic
- **Détection d'incohérences:**
  - Stocks négatifs (erreur critique)
  - Dates incohérentes (livraison avant commande)
  - Quantités négatives dans commandes
  - Lead times anormalement longs/courts

- **Double Persona (V1):**
  - **Mode Opérationnel:** Focus exécution, ruptures, alertes urgentes, détails tactiques
  - **Mode Directeur:** Focus stratégie, financier (BFR, coûts), synthèse haute, KPIs

- **Analyse Temporelle (V1):**
  - Injection date système dans contexte LLM
  - Détection tendances et saisonnalité
  - Calcul délais (lead times, retards)

## Important Constraints

### 1. Confidentialité CRITIQUE (Niveau 0)
- **Rétention maximale:** 24 heures exactement
- **Purge automatique:**
  - Fichiers uploadés: MinIO TTL 24h
  - Index vectoriel: TypeSense TTL natif (86400s)
  - Conversations: PostgreSQL + pg_cron cleanup
- **Self-hosting obligatoire:** Données ne doivent jamais quitter l'infrastructure contrôlée
- **Argument commercial:** Données sensibles Supply Chain (prévisions, contrats, marges)

### 2. Anti-Hallucination CRITIQUE
- **RAG strict:** Toutes réponses doivent être ancrées sur documents fournis
- **Citations obligatoires:** Affichage systématique des sources
- **Température LLM:** 0.1 (max 0.3 pour créativité V2)
- **Validation:** Alerter si LLM ne trouve pas de source fiable

### 3. Précision Citations Excel CRITIQUE
- **Granularité:** Accès cellule par cellule (ex: "C12")
- **Contexte enrichi:** Inclure ligne précédente/suivante si pertinent
- **Métadonnées requises:** Fichier + Feuille + Cellule + Valeur

### 4. Performance
- **Latence chat:** < 2s pour première réponse streaming
- **Latence recherche TypeSense:** < 50ms
- **Upload:** Support fichiers jusqu'à 50MB (Phase MVP)
- **Concurrent users:** 10-20 simultanés (MVP), 100+ (V1)

### 5. Business Constraints
- **Pas de connexion ERP/WMS:** Phase MVP/V1 - fichiers uniquement
- **Pas de données marché externes:** Phase MVP/V1
- **Budget infra:** ~$150-350/mois (MVP)

## External Dependencies

### LLM APIs
- **OpenAI API:**
  - Models: gpt-4-turbo, gpt-3.5-turbo (fallback)
  - Embeddings: text-embedding-3-small (1536 dim)
  - Rate limits: À surveiller (coût variable)

- **Anthropic Claude API:**
  - Models: claude-3-opus, claude-3-sonnet
  - Considéré pour fiabilité supérieure (Phase V1)

### Infrastructure Services
- **TypeSense:** v27.0+ (self-hosted Docker)
- **PostgreSQL:** v15+ (managed ou Docker)
- **Redis:** v7+ (managed ou Docker)
- **MinIO:** Latest (S3-compatible, Docker)

### Document Libraries
- **openpyxl:** v3.1.2+ (Excel read/write)
- **pandas:** v2.2.0+ (data analysis)
- **PyPDF2:** v3.0.1+ (PDF parsing)
- **python-docx:** v1.1.0+ (Word)
- **python-pptx:** v0.6.23+ (PowerPoint)

### Python Backend Stack
```python
# Core dependencies (pyproject.toml)
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
pydantic = "^2.5.0"
langchain = "^0.1.0"
langchain-openai = "^0.0.5"
langchain-anthropic = "^0.1.0"
typesense = "^0.17.0"
langchain-community = "^0.0.16"
sqlalchemy = "^2.0.25"
celery = {extras = ["redis"], version = "^5.3.6"}
```

### Monitoring & Observability (Phase V1)
- **Logs:** Structured logging (structlog)
- **Metrics:** Prometheus + Grafana (à définir)
- **Tracing:** OpenTelemetry (à évaluer)
- **Alerting:** Slack/Email pour purges manquées, erreurs critiques

### Development Tools
- **Package Management:** Poetry (Python), pnpm (Node.js)
- **Linting:** black, mypy, ESLint, Prettier
- **Pre-commit:** Hooks pour formatting + linting
- **CI/CD:** GitHub Actions (à configurer Phase V1)
