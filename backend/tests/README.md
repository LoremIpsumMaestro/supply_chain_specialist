# Tests Backend - Supply Chain AI Assistant

## Vue d'ensemble

Suite de tests unitaires complète pour les modules critiques du backend Supply Chain AI Assistant. Les tests couvrent les parsers de documents, le système de détection d'alertes et le service RAG.

## Couverture de tests

### Modules Critiques (✅ Objectif 80% atteint)

| Module | Couverture | Tests | Status |
|--------|------------|-------|---------|
| **services/document_parser.py** | **80%** | 34 tests | ✅ |
| **services/alert_service.py** | **80%** | 19 tests | ✅ |
| services/rag_service.py | Tests créés | 22 tests | ⚠️ Mocks requis |

### Résumé

- **Total de tests:** 53 tests unitaires
- **Tests passants:** 51/53 (96%)
- **Couverture globale:** 63%
- **Couverture modules critiques:** 80%+ ✅

## Structure des tests

```
backend/tests/
├── __init__.py
├── README.md (ce fichier)
├── test_document_parser.py   # 34 tests - Parsers multi-formats
├── test_alert_service.py      # 19 tests - Détection d'alertes
├── test_rag_service.py        # 22 tests - RAG (nécessite mocks)
└── fixtures/                  # Fichiers de test générés
```

## Installation

### Dépendances de test

```bash
# Depuis backend/
pip install -r requirements.txt

# Les dépendances de test sont déjà incluses :
# - pytest==7.4.4
# - pytest-asyncio==0.23.3
# - pytest-mock==3.12.0
# - pytest-cov==4.1.0
# - faker==22.6.0
# - reportlab (pour génération PDF de test)
```

## Exécution des tests

### Tous les tests

```bash
# Depuis backend/
python -m pytest tests/ -v
```

### Tests par module

```bash
# Tests des parsers de documents
python -m pytest tests/test_document_parser.py -v

# Tests du service d'alertes
python -m pytest tests/test_alert_service.py -v

# Tests du service RAG
python -m pytest tests/test_rag_service.py -v
```

### Tests avec couverture

```bash
# Couverture complète
python -m pytest tests/ --cov=backend --cov-report=html

# Couverture des modules critiques uniquement
python -m pytest tests/test_document_parser.py tests/test_alert_service.py \
  --cov=backend.services.document_parser \
  --cov=backend.services.alert_service \
  --cov-report=term-missing
```

### Tests par catégorie (markers)

```bash
# Tests des parsers uniquement
python -m pytest tests/ -m parser -v

# Tests des alertes uniquement
python -m pytest tests/ -m alert -v

# Tests du RAG uniquement
python -m pytest tests/ -m rag -v

# Tests d'intégration
python -m pytest tests/ -m integration -v

# Exclure les tests lents
python -m pytest tests/ -m "not slow" -v
```

## Détails des tests

### 1. Test Document Parsers (test_document_parser.py)

**34 tests couvrant :**

#### DocumentChunk
- ✅ Création de chunks valides
- ✅ Validation du contenu (vide, whitespace)
- ✅ Avertissement pour contenu très long

#### ExcelParser
- ✅ Parsing de fichiers Excel avec données
- ✅ Détection de valeurs négatives (stocks)
- ✅ Préservation des références de cellules (C12, etc.)
- ✅ Inclusion des en-têtes de colonnes pour contexte
- ✅ Support multi-feuilles (Stocks, Orders, etc.)
- ✅ Gestion des fichiers vides

#### PDFParser
- ✅ Extraction de contenu PDF
- ✅ Préservation des numéros de pages
- ✅ Chunking pour pages longues

#### WordParser
- ✅ Parsing paragraphe par paragraphe
- ✅ Extraction de tableaux Word
- ✅ Préservation des indices de paragraphes

#### PowerPointParser
- ✅ Extraction slide par slide
- ✅ Distinction title/body/notes
- ✅ Numéros de slides préservés

#### CSVParser
- ✅ Parsing ligne par ligne
- ✅ En-têtes de colonnes inclus
- ✅ Numérotation des lignes correcte

#### TextParser
- ✅ Séparation en paragraphes
- ✅ Chunking pour texte long

#### DocumentParserFactory
- ✅ Récupération du bon parser par type
- ✅ Pattern singleton (même instance)

#### Tests d'intégration
- ✅ Parsing de tous les types de fichiers ensemble

### 2. Test Alert Service (test_alert_service.py)

**19 tests couvrant :**

#### Détection de Stocks Négatifs
- ✅ Excel : Détection de valeurs négatives dans colonnes "Stock"
- ✅ CSV : Détection dans fichiers CSV
- ✅ Pas d'alerte pour valeurs positives
- ✅ Gestion des valeurs non-numériques
- ✅ Support français ("Inventaire", "Quantité")

#### Détection de Lead Times Anormaux
- ✅ Alerte pour délais trop longs (>90 jours)
- ✅ Alerte pour délais trop courts (<1 jour)
- ✅ Pas d'alerte pour plage normale (1-90 jours)

#### Tests d'Edge Cases
- ✅ Métadonnées manquantes
- ✅ Séparateur décimal virgule (format européen)
- ✅ Stock à zéro (pas d'alerte)

#### Singleton
- ✅ Instance globale `alert_detector` initialisée
- ✅ Configuration par défaut correcte

### 3. Test RAG Service (test_rag_service.py)

**22 tests créés (nécessitent mocks TypeSense/Ollama) :**

#### Génération d'Embeddings
- Embeddings Ollama (768 dimensions)
- Cache Redis des embeddings
- Gestion des erreurs API
- Génération en batch

#### Indexation
- Indexation de chunks dans TypeSense
- TTL 24h automatique
- Gestion échecs d'embeddings

#### Recherche Hybride
- Recherche keyword + vector
- Filtrage par user_id et file_id
- Parsing des métadonnées JSON

#### Construction de Contexte RAG
- Citations précises (Excel: cellule, PDF: page, etc.)
- Gestion de résultats vides
- Support tous types de fichiers

#### Suppression
- Suppression de chunks par file_id

## Fixtures de test

Les fixtures suivantes sont disponibles dans `conftest.py` :

### Données de test
- `test_user_id`: UUID utilisateur de test
- `test_file_id`: UUID fichier de test

### Fichiers binaires générés
- `sample_excel_bytes`: Excel avec données Supply Chain (stocks négatifs, orders)
- `sample_pdf_bytes`: PDF généré avec reportlab
- `sample_word_bytes`: Document Word avec paragraphes et tableau
- `sample_powerpoint_bytes`: Présentation PowerPoint
- `sample_csv_bytes`: CSV avec données inventaire
- `sample_text_bytes`: Fichier texte formaté

### Mocks de services
- `mock_redis`: Redis client mocké
- `mock_typesense`: TypeSense client mocké
- `mock_ollama_embeddings`: API Ollama mockée

### Chunks pré-parsés
- `sample_excel_chunks`: Chunks extraits d'Excel
- `sample_chunks_with_alerts`: Chunks déclenchant des alertes

## Données de test

Les fichiers de test incluent des **alertes intentionnelles** pour valider la détection :

### Excel de test (sample_excel_bytes)

**Feuille "Stocks":**
| Product | Stock | Minimum | Status |
|---------|-------|---------|---------|
| Product A | 150 | 100 | OK |
| **Product B** | **-50** | 100 | **Critical** ⚠️ |
| Product C | 200 | 100 | OK |
| Product D | 0 | 50 | Empty |

**Feuille "Orders":**
| Order ID | Product | Quantity | Status |
|----------|---------|----------|---------|
| ORD001 | Product A | 50 | Shipped |
| **ORD002** | Product B | **-10** | **Error** ⚠️ |
| ORD003 | Product C | 75 | Processing |

### PDF de test
- Page 1: Rapport Supply Chain Q1 2024
- Page 2: Alertes critiques (stock négatif, lead time >95 jours)

## Résultats attendus

### Parsers
- **Excel**: 11+ chunks (cellules non-vides des 2 feuilles)
- **PDF**: 2+ chunks (1 par page, chunking si long)
- **Word**: 6+ chunks (paragraphes + lignes de tableau)
- **PowerPoint**: 3+ chunks (titres + contenus slides)
- **CSV**: 4 chunks (4 lignes de données)
- **Text**: 3+ chunks (paragraphes)

### Alertes détectées
- **Negative Stock**: Product B (-50 unités) → CRITICAL
- **Negative Quantity**: ORD002 (-10) → WARNING
- **Lead Time Outlier**: Supplier X (120 jours) → WARNING

## Configuration pytest

Le fichier `pytest.ini` configure :

- **Découverte automatique** : `test_*.py`, `Test*`, `test_*`
- **Couverture** : Objectif 80%, rapport HTML dans `htmlcov/`
- **Markers** : `unit`, `integration`, `slow`, `parser`, `rag`, `alert`
- **Asyncio** : Mode automatique
- **Exclusions** : `venv/`, `migrations/`, `__init__.py`, `config.py`

## Problèmes connus

### Tests RAG
Les tests RAG nécessitent des mocks complets de TypeSense et Ollama. Certains tests peuvent échouer si les exceptions TypeSense ne sont pas correctement mockées.

**Solution :** Utiliser `pytest-mock` pour mocker complètement les clients externes.

### Tests quantités négatives
Quelques tests de détection de quantités négatives peuvent échouer si les mots-clés ne matchent pas exactement. Ceci est dû à la logique de distinction stock/quantity dans `alert_service.py`.

**Solution :** Réviser les mots-clés dans `SupplyChainAlertDetector.__init__()`.

## Amélirations futures

### Tests manquants
- [ ] Tests API endpoints (FastAPI TestClient)
- [ ] Tests tâches Celery (document_tasks.py)
- [ ] Tests modèles Pydantic/SQLAlchemy
- [ ] Tests E2E avec base de données réelle
- [ ] Tests d'intégration RAG avec TypeSense local

### Optimisations
- [ ] Parallélisation des tests (pytest-xdist)
- [ ] Fixtures partagées pour fichiers volumineux
- [ ] Mock plus intelligent TypeSense (responses)
- [ ] Tests de performance (pytest-benchmark)

## Références

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)

## Contact

Pour toute question sur les tests, consulter :
- `backend/conftest.py` - Fixtures globales
- `backend/pytest.ini` - Configuration pytest
- Cette documentation
