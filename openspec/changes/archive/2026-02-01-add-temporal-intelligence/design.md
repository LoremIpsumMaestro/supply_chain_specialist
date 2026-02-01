# Design: Temporal Intelligence

## Context

Les données Supply Chain sont intrinsèquement temporelles : commandes, livraisons, stocks évoluent dans le temps. Sans contexte temporel, le LLM ne peut pas distinguer des données récentes des données obsolètes, ni calculer des métriques critiques comme les délais de livraison ou détecter des tendances saisonnières.

### Stakeholders
- **Utilisateurs Opérationnels** : Besoin de calculs de délais précis (retards, lead times)
- **Utilisateurs Directeurs** : Besoin d'analyse de tendances et saisonnalité pour planification stratégique

### Constraints
- Performance : Ne pas ajouter > 500ms de latence au pipeline RAG
- Confidentialité : Les calculs temporels doivent respecter la purge 24h
- Simplicité : Détection automatique doit fonctionner dans 80%+ des cas sans configuration manuelle

## Goals / Non-Goals

### Goals
1. Injection automatique de la date système dans tous les prompts LLM
2. Détection automatique des colonnes temporelles (dates) dans Excel/CSV
3. Calcul automatique des lead times et retards
4. Analyse de tendances et saisonnalité sur séries temporelles
5. Fallback manuel si détection automatique échoue

### Non-Goals
- ❌ Support des fuseaux horaires multiples (UTC only pour MVP)
- ❌ Jours ouvrés vs calendaires (calendaires pour MVP, ouvrés en V2)
- ❌ Prévisions temporelles (What-If) : Phase V2
- ❌ Connexion à sources temps réel (ERP/WMS) : Phase V2+

## Decisions

### Decision 1: Format d'injection de la date système

**Choix** : Injection dans le prompt système avec format français lisible

```python
system_content += f"\nDATE ACTUELLE: {datetime.now().strftime('%d %B %Y')} (exemple: 29 janvier 2026)\n"
```

**Alternatives considérées**:
- ❌ Format ISO 8601 (`2026-01-29`) : Moins lisible pour le LLM français
- ❌ Timestamp Unix : Illisible, nécessite conversion par le LLM
- ✅ Format français avec nom du mois : Optimal pour compréhension LLM

**Rationale** : Les tests montrent que les LLM comprennent mieux les dates en langage naturel.

---

### Decision 2: Heuristiques de détection colonnes temporelles

**Choix** : Multi-critères (nom + type + format)

**Patterns de noms de colonnes** (case-insensitive):
```python
DATE_COLUMN_PATTERNS = [
    r'date',
    r'delivery.*date', r'livraison', r'reception',
    r'order.*date', r'commande',
    r'ship.*date', r'expedition',
    r'due.*date', r'echeance',
    r'timestamp', r'datetime',
]
```

**Validation de format** :
- Excel : Type `datetime` natif OU format `dd/mm/yyyy`, `yyyy-mm-dd`, `dd-mm-yyyy`
- CSV : Parsing avec `dateutil.parser` (tolère formats variés)

**Alternatives considérées**:
- ❌ Nom de colonne seulement : Trop de faux positifs (ex: "update_user")
- ❌ Type seulement : Ne marche pas en CSV (tout est string)
- ✅ Combinaison nom + format + type : Robuste

---

### Decision 3: Stockage des métadonnées temporelles

**Choix** : Nouveau champ JSONB `temporal_metadata` dans table `files`

```sql
ALTER TABLE files ADD COLUMN temporal_metadata JSONB;
```

**Structure**:
```json
{
  "upload_date": "2026-01-29T10:30:00Z",
  "detected_date_columns": ["date_commande", "date_livraison"],
  "user_configured_columns": null,
  "time_range": {
    "earliest": "2025-06-01",
    "latest": "2026-01-15"
  },
  "lead_time_stats": {
    "mean_days": 12.5,
    "median_days": 10,
    "max_days": 45,
    "outliers": [45, 38]
  }
}
```

**Alternatives considérées**:
- ❌ Table séparée `temporal_metadata` : Over-engineering pour MVP
- ❌ Stockage dans TypeSense metadata : Difficile à requêter pour config UI
- ✅ JSONB dans table files : Simple, flexible, facile à étendre

---

### Decision 4: Calcul des lead times

**Choix** : Paires de colonnes détectées automatiquement

**Logique**:
1. Détecter toutes colonnes temporelles
2. Si 2 colonnes exactement → Assumer `(start, end)` et calculer delta
3. Si >2 colonnes → Chercher patterns courants:
   - `(order_date, delivery_date)` → Lead time
   - `(ship_date, received_date)` → Transit time
4. Si ambigu → Proposer configuration manuelle

**Alternatives considérées**:
- ❌ Toujours demander configuration : Friction utilisateur
- ❌ Ne calculer que si noms exacts ("order_date") : Trop restrictif
- ✅ Heuristique + fallback : Balance automatisation et flexibilité

---

### Decision 5: Analyse de tendances

**Choix** : Calculs simples stockés dans chunks metadata

**Métriques calculées**:
- **Moyenne glissante** (7 jours, 30 jours)
- **Variation** : % change vs période précédente
- **Détection saisonnalité** : Si données ≥6 mois, calculer moyenne par mois

**Stockage** : Enrichir metadata de chunks avec résultats calculs

```python
chunk.metadata = {
  "filename": "ventes.xlsx",
  "sheet_name": "2025",
  "cell_ref": "C12",
  "value": 150,
  "temporal_context": {
    "date": "2025-12-15",
    "rolling_avg_7d": 145,
    "rolling_avg_30d": 120,
    "vs_previous_month": "+25%",
    "seasonal_pattern": "Pic annuel (décembre)"
  }
}
```

**Alternatives considérées**:
- ❌ Service séparé pour calculs à la volée : Trop lent (>1s)
- ❌ Pre-calcul de toutes métriques possibles : Gaspillage CPU/stockage
- ✅ Calculs basiques pré-indexés : Balance performance/utilité

---

### Decision 6: API Configuration manuelle

**Choix** : Endpoint PATCH pour override colonnes détectées

```
PATCH /api/files/{file_id}/temporal-config
Body: {
  "date_columns": ["col_commande", "col_livraison"],
  "lead_time_pairs": [["col_commande", "col_livraison"]]
}
```

**Workflow**:
1. Upload fichier → Détection auto → Stockage dans `temporal_metadata.detected_date_columns`
2. Si détection OK → Utilisateur voit les colonnes détectées, peut valider
3. Si détection manquante/fausse → Utilisateur PATCH pour corriger
4. Re-indexation automatique avec nouvelles colonnes

**Alternatives considérées**:
- ❌ Configuration avant upload : Friction UX
- ❌ Pas de configuration manuelle : Bloquant si heuristique échoue
- ✅ Auto + fallback : Meilleure UX

## Risks / Trade-offs

### Risk 1: Faux positifs dans détection colonnes
**Impact** : Colonne "update_date" détectée comme date métier → Calculs incorrects

**Mitigation**:
- Blacklist de patterns à ignorer (`created_at`, `updated_at`, `deleted_at`, `last_modified`)
- Validation: Vérifier que ≥10% des cellules sont remplies (sinon ignorer colonne)
- UI de validation : Afficher colonnes détectées, demander confirmation

---

### Risk 2: Performance sur gros fichiers
**Impact** : Fichier Excel 50k lignes × 10 colonnes → 500k cellules à analyser

**Mitigation**:
- Sampling : Analyser seulement les 1000 premières lignes pour détection
- Lazy loading : Calculs tendances seulement si requête utilisateur mentionne "tendance" ou "évolution"
- Timeouts : Limiter calculs à 5s max par fichier

---

### Risk 3: Qualité données utilisateur
**Impact** : Dates incohérentes (2025-02-30), formats mixtes (01/02/2025 vs 2025-02-01)

**Mitigation**:
- Parsing robuste avec `dateutil.parser` (tolère formats variés)
- Validation : Skip lignes avec dates invalides, logger warning
- Alerte utilisateur : Si >20% dates invalides → "Fichier contient des dates incohérentes"

## Migration Plan

### Phase 1: Backend Infrastructure (Week 1)
1. Créer `backend/services/temporal_service.py`
2. Ajouter migration DB (`006_add_temporal_metadata.sql`)
3. Implémenter heuristiques détection colonnes
4. Tests unitaires

### Phase 2: RAG Integration (Week 1)
1. Modifier `llm_service.py` : Injection date système
2. Modifier `document_parser.py` : Appeler `temporal_service` après parsing
3. Enrichir chunks metadata avec contexte temporel
4. Tests intégration

### Phase 3: API & Frontend (Week 2)
1. Endpoint PATCH `/api/files/{file_id}/temporal-config`
2. Endpoint GET `/api/files/{file_id}/temporal-metadata`
3. Frontend : Afficher colonnes détectées + UI configuration manuelle
4. Tests E2E

### Rollback Strategy
- Si bug critique → Feature flag `ENABLE_TEMPORAL_ANALYSIS=false`
- Champ `temporal_metadata` nullable → Pas de blocage si null
- Fallback graceful : Si calculs échouent, continuer sans contexte temporel

## Open Questions

### Q1: Fuseaux horaires
**Question** : Comment gérer les fuseaux horaires ?

**Options**:
- A) Tout en UTC (simple, perd contexte local)
- B) Détecter timezone du système (complexe, bug-prone)
- C) Configuration utilisateur (friction UX)

**Recommandation** : A pour MVP, C en V2 si demande utilisateurs

---

### Q2: Jours ouvrés vs calendaires
**Question** : Calculer lead times en jours ouvrés (5j/semaine) ou calendaires (7j/semaine) ?

**Options**:
- A) Jours calendaires (simple, universel)
- B) Jours ouvrés avec calendrier français (complexe, jours fériés)

**Recommandation** : A pour MVP, B en V2 avec configuration calendrier

---

### Q3: Seuil détection saisonnalité
**Question** : Minimum de données pour détecter saisonnalité fiable ?

**Options**:
- A) 6 mois (2 saisons)
- B) 12 mois (1 an complet)
- C) 24 mois (2 ans pour confirmation)

**Recommandation** : A pour MVP (balance utilité/fiabilité)
