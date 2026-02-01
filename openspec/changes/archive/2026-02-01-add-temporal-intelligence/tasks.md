# Implementation Tasks: Temporal Intelligence

## Overview
Implémentation de l'intelligence temporelle en 3 phases : Backend infrastructure, RAG integration, et API/Frontend.

**Durée estimée totale**: 2 semaines (10 jours)

---

## Phase 1: Backend Infrastructure (Semaine 1)

### Task 1.1: Create Temporal Service ✅
**Description**: Créer le service temporel avec heuristiques de détection colonnes et calculs.

**Steps**:
1. Créer `backend/services/temporal_service.py` avec classe `TemporalService`
2. Implémenter méthodes:
   - `detect_temporal_columns(df: DataFrame, column_names: List[str]) -> List[str]`
   - `calculate_lead_times(df: DataFrame, start_col: str, end_col: str) -> Dict`
   - `extract_time_range(df: DataFrame, temporal_cols: List[str]) -> Dict`
   - `calculate_trends(df: DataFrame, date_col: str, value_col: str) -> Dict`
3. Patterns de détection:
   ```python
   DATE_COLUMN_PATTERNS = [
       r'date', r'delivery.*date', r'livraison', r'reception',
       r'order.*date', r'commande', r'ship.*date', r'expedition',
       r'due.*date', r'echeance', r'timestamp', r'datetime',
   ]
   BLACKLIST_PATTERNS = [r'created_at', r'updated_at', r'deleted_at', r'last_modified']
   ```
4. Validation: ≥80% cellules non vides doivent être des dates valides
5. Timeout: Maximum 5s par fichier pour calculs

**Validation**:
- Test avec Excel 100 lignes × 5 colonnes → Détecte colonnes en <200ms
- Test lead time calculation → Calcule mean, median, max, outliers
- Test saisonnalité avec 12 mois de données → Détecte pic décembre

**Estimated Effort**: 2 jours

---

### Task 1.2: Database Migration for Temporal Metadata ✅
**Description**: Ajouter champ temporal_metadata à la table files.

**Steps**:
1. Créer migration `006_add_temporal_metadata.sql`:
   ```sql
   ALTER TABLE files ADD COLUMN temporal_metadata JSONB;
   CREATE INDEX idx_files_temporal_metadata ON files USING GIN (temporal_metadata);
   ```
2. Mettre à jour modèle `backend/models/file.py`:
   ```python
   class FileDB(Base):
       ...
       temporal_metadata: Optional[dict] = Column(JSONB, nullable=True)
   ```
3. Pydantic schema pour validation:
   ```python
   class TemporalMetadata(BaseModel):
       upload_date: datetime
       detected_date_columns: List[str]
       user_configured_columns: Optional[List[str]]
       time_range: Optional[Dict[str, str]]  # {earliest, latest}
       lead_time_stats: Optional[Dict[str, float]]  # {mean, median, max, outliers}
   ```

**Validation**:
- Migration up/down fonctionne
- Champ temporal_metadata nullable (rétro-compatibilité)
- Index GIN créé pour requêtes JSONB

**Estimated Effort**: 0.5 jour

---

### Task 1.3: Unit Tests for Temporal Service ✅
**Description**: Tests unitaires complets pour temporal_service.py.

**Steps**:
1. Créer `backend/tests/test_temporal_service.py`
2. Tests de détection:
   - `test_detect_date_columns_by_name()` : Colonnes "date_commande", "date_livraison"
   - `test_detect_date_columns_by_format()` : Validation format DD/MM/YYYY
   - `test_ignore_blacklisted_columns()` : Skip "created_at", "updated_at"
   - `test_sparse_temporal_data()` : Rejeter colonnes avec <10% données valides
3. Tests lead times:
   - `test_calculate_lead_times_auto_pair()` : 2 colonnes → auto-pairing
   - `test_detect_outliers()` : Flaguer valeurs >2 std dev
4. Tests tendances:
   - `test_rolling_averages()` : Moyennes glissantes 7j, 30j
   - `test_seasonal_detection()` : Pic décembre sur 12 mois
   - `test_insufficient_data()` : Skip si <6 mois
5. Tests performance:
   - `test_detection_performance()` : <200ms pour 1000 lignes
   - `test_timeout()` : Abort si >5s

**Validation**:
- Coverage ≥90% pour temporal_service.py
- Tous tests passent

**Estimated Effort**: 1.5 jour

---

## Phase 2: RAG Integration (Semaine 1)

### Task 2.1: Inject System Date in LLM Prompts ✅
**Description**: Modifier llm_service.py pour injecter la date système dans tous les prompts.

**Steps**:
1. Modifier `backend/services/llm_service.py` méthode `_build_messages()`:
   ```python
   from datetime import datetime
   import locale

   def _build_messages(self, conversation_history, rag_context=""):
       # Set French locale for month names
       locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
       current_date = datetime.now().strftime('%d %B %Y')

       system_content = (
           f"DATE ACTUELLE: {current_date}\n\n"
           "Tu es un assistant IA spécialisé en Supply Chain. ..."
       )
       ...
   ```
2. Fallback si locale fr_FR non disponible → Format anglais
3. Logging: Log date injectée pour debugging

**Validation**:
- Test prompt contient "DATE ACTUELLE: 29 janvier 2026"
- Test avec query "Cette livraison est-elle en retard?" → LLM utilise date système

**Estimated Effort**: 0.5 jour

---

### Task 2.2: Enrich Document Chunks with Temporal Metadata ✅
**Description**: Modifier document_parser.py pour appeler temporal_service et enrichir chunks.

**Steps**:
1. Modifier `backend/services/document_parser.py`:
   - Dans `ExcelParser.parse()`:
     ```python
     # After parsing all chunks
     from backend.services.temporal_service import temporal_service

     # Detect temporal columns
     temporal_cols = temporal_service.detect_temporal_columns(df, df.columns.tolist())

     # Calculate lead times if applicable
     lead_time_stats = None
     if len(temporal_cols) == 2:
         lead_time_stats = temporal_service.calculate_lead_times(df, temporal_cols[0], temporal_cols[1])

     # Enrich chunks with temporal context
     for chunk in chunks:
         row_idx = chunk.metadata['row']
         chunk.metadata['temporal_context'] = {
             'date': df.iloc[row_idx][temporal_cols[0]] if temporal_cols else None,
             'lead_time_days': lead_time_stats.get('per_row', {}).get(row_idx) if lead_time_stats else None
         }
     ```
   - Répéter pour `CSVParser.parse()`
2. Ajouter `upload_date` à tous chunks:
   ```python
   chunk.metadata['upload_date'] = datetime.utcnow().isoformat()
   ```

**Validation**:
- Upload Excel avec colonnes date → Chunks contiennent `temporal_context`
- Upload PDF → Chunks contiennent `upload_date` mais pas `temporal_context`

**Estimated Effort**: 1.5 jour

---

### Task 2.3: Store Temporal Metadata in Files Table ✅
**Description**: Stocker temporal_metadata lors du processing asynchrone.

**Steps**:
1. Modifier `backend/tasks/document_tasks.py` task `process_document()`:
   ```python
   @celery_app.task
   def process_document(file_id: str):
       # ... existing parsing logic ...

       # After parsing, extract temporal metadata
       temporal_metadata = {
           'upload_date': datetime.utcnow().isoformat(),
           'detected_date_columns': temporal_service.get_detected_columns(chunks),
           'user_configured_columns': None,
           'time_range': temporal_service.extract_time_range(chunks),
           'lead_time_stats': temporal_service.get_lead_time_stats(chunks),
       }

       # Update file record
       file_db.temporal_metadata = temporal_metadata
       db.commit()
   ```

**Validation**:
- Upload fichier → temporal_metadata sauvegardée en DB
- Query `SELECT temporal_metadata FROM files WHERE id = ...` retourne JSON

**Estimated Effort**: 0.5 jour

---

### Task 2.4: Include Temporal Context in RAG Results ✅
**Description**: Modifier rag_service.py pour inclure temporal_context dans résultats.

**Steps**:
1. Modifier `backend/services/rag_service.py` méthode `build_rag_context()`:
   ```python
   def build_rag_context(self, search_results: List[Dict]) -> str:
       context_parts = []

       for idx, result in enumerate(search_results, start=1):
           metadata = result['metadata']

           # Format source with temporal context
           source = self._format_source_citation(metadata, idx)

           # Add temporal metrics if available
           if 'temporal_context' in metadata:
               tc = metadata['temporal_context']
               temporal_info = []
               if tc.get('date'):
                   temporal_info.append(f"date: {tc['date']}")
               if tc.get('rolling_avg_30d'):
                   temporal_info.append(f"moyenne 30j: {tc['rolling_avg_30d']}")
               if tc.get('vs_previous_month'):
                   temporal_info.append(f"évolution: {tc['vs_previous_month']}")

               if temporal_info:
                   source += f" ({', '.join(temporal_info)})"

           context_parts.append(f"{source}\n{result['content']}\n")

       return "\n".join(context_parts)
   ```

**Validation**:
- RAG search avec chunks temporels → Context inclut dates et métriques
- LLM response mentionne tendances (ex: "+25% vs mois précédent")

**Estimated Effort**: 1 jour

---

## Phase 3: API & Frontend (Semaine 2)

### Task 3.1: API Endpoints for Temporal Configuration ✅
**Description**: Créer endpoints PATCH et GET pour configuration manuelle.

**Steps**:
1. Créer `backend/api/temporal.py` avec endpoints:
   ```python
   @router.get("/files/{file_id}/temporal-metadata")
   async def get_temporal_metadata(file_id: str, current_user: User = Depends(get_current_user)):
       file = db.query(FileDB).filter(FileDB.id == file_id, FileDB.user_id == current_user.id).first()
       if not file:
           raise HTTPException(404)
       return file.temporal_metadata

   @router.patch("/files/{file_id}/temporal-config")
   async def update_temporal_config(
       file_id: str,
       config: TemporalConfigUpdate,
       current_user: User = Depends(get_current_user)
   ):
       # Update temporal_metadata with user config
       # Trigger re-indexing with new temporal context
   ```
2. Pydantic schema `TemporalConfigUpdate`:
   ```python
   class TemporalConfigUpdate(BaseModel):
       date_columns: Optional[List[str]]
       lead_time_pairs: Optional[List[Tuple[str, str]]]
   ```
3. Re-indexation: Appeler `process_document.delay(file_id)` après PATCH

**Validation**:
- PATCH avec nouvelles colonnes → temporal_metadata updated
- GET retourne metadata complète

**Estimated Effort**: 1 jour

---

### Task 3.2: Frontend UI for Temporal Column Validation ✅
**Description**: Afficher colonnes détectées et permettre configuration manuelle.

**Steps**:
1. Créer composant `frontend/components/file/TemporalMetadataPanel.tsx`:
   - Fetch `/api/files/{file_id}/temporal-metadata`
   - Afficher colonnes détectées
   - Checkbox pour chaque colonne (enable/disable)
   - Bouton "Recalculer" → PATCH `/api/files/{file_id}/temporal-config`
2. Intégrer dans la page de détails fichier ou modal après upload
3. Afficher time range et lead time stats si disponibles

**Validation**:
- Upload fichier → Panel affiche colonnes détectées
- User décoche colonne "updated_at" → PATCH envoyé
- Colonnes mises à jour visibles après refresh

**Estimated Effort**: 1.5 jour

---

### Task 3.3: Display Temporal Context in Citations ✅
**Description**: Modifier Citation.tsx pour afficher contexte temporel.

**Steps**:
1. Modifier `frontend/components/chat/Citation.tsx`:
   ```tsx
   interface CitationProps {
     citation: CitationMetadata;
   }

   export function Citation({ citation }: CitationProps) {
     const { filename, sheet_name, cell_ref, page, temporal_context } = citation;

     return (
       <div className="citation">
         <span className="source">
           {filename} {sheet_name && `- ${sheet_name}`} {cell_ref && `- ${cell_ref}`}
         </span>

         {temporal_context && (
           <span className="temporal-info text-sm text-gray-600">
             {temporal_context.date && `📅 ${temporal_context.date}`}
             {temporal_context.vs_previous_month && ` (${temporal_context.vs_previous_month})`}
           </span>
         )}

         <p className="excerpt">{citation.excerpt}</p>
       </div>
     );
   }
   ```
2. Mettre à jour type `CitationMetadata` pour inclure `temporal_context`

**Validation**:
- Citation avec temporal_context → Affiche date et variation
- Citation sans temporal_context → Affichage normal

**Estimated Effort**: 0.5 jour

---

### Task 3.4: Integration Tests ✅
**Description**: Tests E2E pour vérifier le flow complet.

**Steps**:
1. Test E2E Playwright:
   - Upload Excel avec colonnes date → Vérifier colonnes détectées
   - Poser question "Quelle est la tendance des ventes?" → Vérifier réponse mentionne variation
   - PATCH configuration colonnes → Vérifier recalcul
2. Test API:
   - POST upload → GET temporal-metadata → Vérifier structure JSON
   - PATCH config → Vérifier re-indexing déclenché

**Validation**:
- Flow complet fonctionne end-to-end
- Performance acceptable (<500ms overhead)

**Estimated Effort**: 1.5 jour

---

### Task 3.5: Documentation ✅
**Description**: Documenter la nouvelle fonctionnalité.

**Steps**:
1. Mettre à jour README.md:
   - Section "Intelligence Temporelle"
   - Exemples de questions temporelles supportées
   - Screenshots colonnes détectées
2. Documenter API endpoints dans OpenAPI spec
3. Ajouter exemples dans QUICKSTART.md

**Validation**:
- Documentation claire et complète
- Screenshots à jour

**Estimated Effort**: 0.5 jour

---

## Summary

**Total Estimated Effort**: 11.5 jours (~2.3 semaines)

**Parallelization Opportunities**:
- Task 1.3 (tests) // Task 2.1 (injection date)
- Task 3.2 (frontend) // Task 3.1 (API)

**Critical Path**:
1.1 → 1.2 → 2.2 → 2.3 → 2.4 → 3.1 → 3.2 → 3.4

**Key Dependencies**:
- Phase 2 dépend de Phase 1 (temporal_service doit exister)
- Phase 3 dépend de Phase 2 (temporal_metadata doit être peuplé)
- Task 3.4 (tests E2E) dépend de tous les autres

**Risk Mitigation**:
- Feature flag: `ENABLE_TEMPORAL_ANALYSIS` pour rollback rapide
- Timeout 5s pour calculs → Pas de blocage si fichiers trop gros
- Graceful fallback: Si temporal_metadata null, continuer sans contexte temporel
