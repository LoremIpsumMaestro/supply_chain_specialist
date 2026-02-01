# Base de Connaissances Permanente

Ce dossier contient le système de gestion de la base de connaissances permanente pour l'Assistant IA Supply Chain.

## 📚 Qu'est-ce que la Base de Connaissances ?

La base de connaissances est un système de stockage permanent de connaissances métier (supply chain, logistique, etc.) qui enrichit les réponses du modèle LLM. Contrairement aux documents uploadés par les utilisateurs (qui ont un TTL de 24h), les connaissances de la base sont **permanentes** et accessibles à tous les utilisateurs.

### Différences avec les Documents Utilisateurs

| Caractéristique | Documents Utilisateurs | Base de Connaissances |
|-----------------|------------------------|------------------------|
| **Durée de vie** | 24 heures (TTL) | Permanente |
| **Visibilité** | Privée (par user_id) | Globale (tous users) |
| **Objectif** | Analyse de données spécifiques | Connaissances métier générales |
| **Collection TypeSense** | `document_chunks` | `knowledge_base` |
| **Gestion** | Upload via UI | Ingestion via CLI |

## 🗂️ Organisation

```
backend/knowledge/
├── README.md                    # Ce fichier
├── examples/                    # Exemples de fichiers de connaissances
│   ├── supply_chain_basics.json
│   ├── kpis_supply_chain.yaml
│   └── best_practices_logistics.md
└── data/                        # Vos fichiers de connaissances (à créer)
    ├── supply_chain/
    ├── logistics/
    └── inventory/
```

## 📝 Formats Supportés

### 1. JSON

Format structuré idéal pour des connaissances bien organisées.

```json
{
  "knowledge_items": [
    {
      "title": "Titre de la connaissance",
      "category": "supply_chain",
      "subcategory": "gestion_stocks",
      "tags": ["stock", "kpi"],
      "content": "Le contenu détaillé de la connaissance...",
      "metadata": {
        "source": "Nom de la source",
        "last_updated": "2026-01"
      }
    }
  ]
}
```

### 2. YAML

Format plus lisible, équivalent au JSON.

```yaml
knowledge_items:
  - title: "Titre de la connaissance"
    category: "supply_chain"
    subcategory: "gestion_stocks"
    tags:
      - stock
      - kpi
    content: |
      Le contenu détaillé de la connaissance...
      Peut être sur plusieurs lignes.
    metadata:
      source: "Nom de la source"
      last_updated: "2026-01"
```

### 3. Markdown

Format idéal pour de la documentation longue. Chaque section (# ou ##) devient une connaissance distincte.

```markdown
# Titre Section 1

Contenu de la première connaissance...

# Titre Section 2

Contenu de la deuxième connaissance...
```

### 4. Texte Brut

Pour des documents simples. Découpé automatiquement en chunks si trop long.

```
Contenu de la connaissance...
```

## 🚀 Ingestion des Connaissances

### Pré-requis

1. **Services lancés** :
   ```bash
   # TypeSense (vector store)
   docker run -d -p 8108:8108 typesense/typesense:27.1

   # Redis (cache embeddings)
   docker run -d -p 6379:6379 redis:alpine

   # Ollama (embeddings)
   ollama serve
   ollama pull nomic-embed-text
   ```

2. **Backend Python** :
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Commandes d'Ingestion

#### Ingérer depuis JSON

```bash
python backend/scripts/ingest_knowledge.py \
  --file backend/knowledge/examples/supply_chain_basics.json
```

#### Ingérer depuis YAML

```bash
python backend/scripts/ingest_knowledge.py \
  --file backend/knowledge/examples/kpis_supply_chain.yaml
```

#### Ingérer depuis Markdown

```bash
python backend/scripts/ingest_knowledge.py \
  --file backend/knowledge/examples/best_practices_logistics.md \
  --category logistics \
  --subcategory best_practices \
  --tags optimisation efficacité
```

#### Ingérer depuis Texte

```bash
python backend/scripts/ingest_knowledge.py \
  --file mon_fichier.txt \
  --title "Guide Lead Times" \
  --category supply_chain \
  --subcategory délais \
  --tags lead_time approvisionnement
```

### Gestion de la Base

#### Lister les catégories

```bash
python backend/scripts/ingest_knowledge.py --list-categories
```

#### Supprimer une catégorie

```bash
python backend/scripts/ingest_knowledge.py --delete-category supply_chain
```

## 🏗️ Architecture

### Schéma TypeSense `knowledge_base`

```python
{
  'knowledge_id': str,        # UUID unique
  'category': str,            # Catégorie principale (indexée)
  'subcategory': str,         # Sous-catégorie (optionnelle, indexée)
  'title': str,               # Titre de la connaissance
  'content': str,             # Contenu textuel
  'embedding': float[768],    # Vecteur d'embedding (nomic-embed-text)
  'metadata': str,            # JSON metadata additionnelle
  'tags': str[],              # Tags optionnels (indexés)
  'created_at': int64,        # Timestamp de création
}
```

### Flux de Recherche

Lorsqu'un utilisateur pose une question :

1. **Recherche Knowledge Base** : Top 3 résultats de connaissances générales
2. **Recherche Documents Utilisateur** : Top 5 résultats de ses documents uploadés (si applicable)
3. **Contexte Combiné** : Les deux sources sont fusionnées dans le prompt du LLM
4. **Citations Distinctes** : Les citations indiquent clairement la source (KB vs documents)

```
User Query
    ↓
┌───────────────────────────────────┐
│  Knowledge Service (Top 3)        │
│  ↓                                │
│  TypeSense: knowledge_base        │
│  Hybrid Search (keyword + vector) │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  RAG Service (Top 5)              │
│  ↓                                │
│  TypeSense: document_chunks       │
│  Hybrid Search (keyword + vector) │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  Combined Context                 │
│  ↓                                │
│  Knowledge Context                │
│  + User Documents Context         │
└───────────────────────────────────┘
    ↓
LLM Response avec Citations
```

## 📊 Catégories Recommandées

### Supply Chain
- **Concepts de base** : définitions, terminologie
- **Gestion des stocks** : méthodes, calculs
- **Approvisionnement** : stratégies, processus
- **Planification** : S&OP, MRP, DRP
- **Risques** : identification, mitigation

### Logistics
- **Transport** : modes, optimisation
- **Entreposage** : layout, picking, packing
- **Distribution** : réseaux, dernière mile

### KPIs & Metrics
- **Performance** : taux de service, rotation
- **Financiers** : TCO, cash-to-cash
- **Qualité** : perfect order, OTIF

### Best Practices
- **Optimisation** : processus, outils
- **Digital** : technologies, IA, IoT
- **Durabilité** : green supply chain

## 🔍 Recherche et Filtrage

Le système supporte la recherche hybride (keyword + sémantique) avec filtrage optionnel.

### API Python

```python
from backend.services.knowledge_service import knowledge_service

# Recherche simple
results = knowledge_service.search_knowledge(
    query="Comment calculer le stock de sécurité ?",
    top_k=5
)

# Recherche avec filtres
results = knowledge_service.search_knowledge(
    query="lead time",
    top_k=5,
    category="supply_chain",
    tags=["approvisionnement"]
)

# Ajouter une connaissance programmatiquement
knowledge_service.add_knowledge(
    content="Le contenu...",
    category="supply_chain",
    title="Ma connaissance",
    subcategory="gestion_stocks",
    tags=["stock", "kpi"]
)
```

## 💡 Bonnes Pratiques

### Contenu des Connaissances

1. **Précision et exactitude** : Vérifier les sources, éviter les approximations
2. **Concision** : Chunks de 200-2000 mots pour des embeddings efficaces
3. **Structuration** : Utiliser des paragraphes clairs avec titres explicites
4. **Contexte suffisant** : Chaque chunk doit être compréhensible seul
5. **Mise à jour régulière** : Maintenir les connaissances à jour

### Organisation

1. **Catégories cohérentes** : Utiliser un vocabulaire standardisé
2. **Tags pertinents** : 3-5 tags par connaissance pour faciliter le filtrage
3. **Métadonnées** : Toujours indiquer la source et la date
4. **Hiérarchie claire** : category > subcategory > tags

### Performance

1. **Batch import** : Pour de gros volumes, utiliser `add_knowledge_batch()`
2. **Cache embeddings** : Redis cache automatiquement les embeddings (24h)
3. **Top-k optimal** : 3-5 résultats suffisent généralement
4. **Monitoring** : Suivre les logs pour les erreurs d'embedding

## 🔧 Développement

### Ajouter un Nouveau Type de Source

1. Créer un nouveau parser dans `document_parser.py` si besoin
2. Modifier `ingest_knowledge.py` pour supporter le format
3. Tester avec des exemples

### Modifier le Schéma TypeSense

1. Supprimer la collection existante :
   ```python
   from backend.services.knowledge_service import knowledge_service
   knowledge_service.typesense_client.collections['knowledge_base'].delete()
   ```

2. Modifier le schéma dans `knowledge_service.py`
3. Redémarrer le service (la collection sera recréée automatiquement)
4. Réingérer les données

## 📈 Exemples d'Usage

### Scénario 1 : Base de Connaissances Initiale

```bash
# 1. Ingérer les connaissances de base
python backend/scripts/ingest_knowledge.py \
  --file backend/knowledge/examples/supply_chain_basics.json

python backend/scripts/ingest_knowledge.py \
  --file backend/knowledge/examples/kpis_supply_chain.yaml

python backend/scripts/ingest_knowledge.py \
  --file backend/knowledge/examples/best_practices_logistics.md \
  --category logistics \
  --tags best_practices

# 2. Vérifier
python backend/scripts/ingest_knowledge.py --list-categories
```

### Scénario 2 : Enrichissement Progressif

```bash
# Ajouter des connaissances métier spécifiques
python backend/scripts/ingest_knowledge.py \
  --file guide_interne_achats.md \
  --category procurement \
  --subcategory processus \
  --tags processus fournisseurs

# Ajouter des définitions sectorielles
python backend/scripts/ingest_knowledge.py \
  --file glossaire_automobile.json
```

### Scénario 3 : Mise à Jour

```bash
# 1. Supprimer l'ancienne version
python backend/scripts/ingest_knowledge.py \
  --delete-category supply_chain

# 2. Ingérer la nouvelle version
python backend/scripts/ingest_knowledge.py \
  --file supply_chain_basics_v2.json
```

## 🐛 Troubleshooting

### TypeSense non disponible

```
Error: TypeSense not available for knowledge base
```

**Solution** : Vérifier que TypeSense est lancé sur le port 8108.

### Embedding failed

```
Warning: Failed to generate embedding for knowledge
```

**Solution** : Vérifier qu'Ollama est lancé et que le modèle `nomic-embed-text` est installé.

### Aucun résultat de recherche

**Causes possibles** :
1. Base de connaissances vide → Ingérer des connaissances
2. Query trop spécifique → Élargir la recherche
3. Catégorie incorrecte → Lister les catégories disponibles

## 📞 Support

Pour toute question ou problème :

1. Consulter les logs : `backend/logs/`
2. Vérifier la documentation API : `backend/services/knowledge_service.py`
3. Exampler les exemples : `backend/knowledge/examples/`

---

**Version** : 1.0
**Dernière mise à jour** : Janvier 2026
