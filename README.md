# Supply Chain AI Assistant

Assistant IA spécialisé pour professionnels Supply Chain avec interface de chat type "ChatGPT".

## 🎯 Fonctionnalités (MVP)

- ✅ Interface de chat fluide avec historique des conversations
- ✅ Streaming des réponses LLM en temps réel
- ✅ Citations précises des sources (Excel, PDF, Word, PowerPoint)
- ✅ Upload de documents multi-formats
- ✅ Purge automatique des données après 24h
- ✅ Design responsive (desktop, tablet, mobile)
- ✅ Gestion des conversations (créer, supprimer, basculer)

## 🕐 Intelligence Temporelle (V1)

- ✅ **Injection automatique de la date système** : Le LLM connaît toujours la date actuelle pour calculer des retards
- ✅ **Détection automatique des colonnes de dates** : Identification intelligente des colonnes temporelles dans Excel/CSV
- ✅ **Calcul automatique des lead times** : Délais entre commandes et livraisons calculés automatiquement
- ✅ **Analyse de tendances** : Moyennes glissantes, variations mensuelles, détection de saisonnalité
- ✅ **Citations enrichies** : Les citations incluent le contexte temporel (dates, variations, tendances)
- ✅ **Configuration manuelle** : Possibilité de corriger les colonnes détectées si nécessaire

## 🏗️ Architecture

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15+
- **Cache:** Redis 7+
- **LLM:** OpenAI API / Anthropic Claude API
- **Document Processing:** pandas, openpyxl, PyPDF2, python-docx, python-pptx

### Frontend
- **Framework:** Next.js 15 + React 19
- **Styling:** TailwindCSS + shadcn/ui
- **State Management:** Zustand
- **Streaming:** Vercel AI SDK compatible

## 🚀 Démarrage Rapide

### Prérequis

- Docker et Docker Compose
- Node.js 20+ (pour développement local)
- Python 3.11+ (pour développement local)

### Configuration

1. **Copier les variables d'environnement**

```bash
cp .env.example .env.local
```

2. **Configurer les clés API dans `.env.local`**

```env
# LLM APIs (au moins une requise)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# JWT Secret (générer une clé aléatoire)
JWT_SECRET_KEY=your-secret-key-here

# Database (déjà configuré pour Docker)
DATABASE_URL=postgresql://supply_chain_user:supply_chain_pass@localhost:5432/supply_chain_ai

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Lancement avec Docker Compose

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f

# Arrêter les services
docker-compose down
```

L'application sera accessible sur:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Développement Local

#### Backend

```bash
cd backend

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
psql -U supply_chain_user -d supply_chain_ai -f db/migrations/001_create_conversations_and_messages.sql
psql -U supply_chain_user -d supply_chain_ai -f db/migrations/002_setup_purge_job.sql
psql -U supply_chain_user -d supply_chain_ai -f db/migrations/003_create_files_table.sql
psql -U supply_chain_user -d supply_chain_ai -f db/migrations/004_create_alerts_table.sql
psql -U supply_chain_user -d supply_chain_ai -f db/migrations/005_create_users_table.sql
psql -U supply_chain_user -d supply_chain_ai -f db/migrations/006_add_temporal_metadata.sql

# Lancer le serveur
python -m backend.main
```

#### Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

## 📁 Structure du Projet

```
projet-C/
├── backend/
│   ├── api/              # Endpoints FastAPI
│   ├── db/               # Migrations et configuration DB
│   ├── models/           # Modèles Pydantic et SQLAlchemy
│   ├── services/         # Services métier (LLM, RAG)
│   ├── utils/            # Utilitaires (auth, rate limiting)
│   ├── main.py           # Point d'entrée FastAPI
│   └── requirements.txt  # Dépendances Python
├── frontend/
│   ├── app/              # Pages Next.js (App Router)
│   ├── components/       # Composants React
│   │   ├── chat/         # Composants chat
│   │   └── ui/           # Composants shadcn/ui
│   ├── lib/              # Utilitaires et API client
│   ├── store/            # Stores Zustand
│   ├── types/            # Types TypeScript
│   └── package.json      # Dépendances Node.js
├── openspec/             # Spécifications OpenSpec
│   └── changes/
│       └── add-chat-interface/
├── docker-compose.yml    # Configuration Docker
├── PRD.md                # Product Requirements Document
└── README.md             # Ce fichier
```

## 🔒 Sécurité

- **Confidentialité:** Purge automatique des données après 24h (conversations, messages, fichiers, index vectoriels)
- **Authentication:** JWT tokens avec validation
- **Rate Limiting:** 10 messages/minute par utilisateur
- **CORS:** Configuré pour origines autorisées uniquement
- **Secrets:** Jamais exposés au client, gérés via variables d'environnement

## 🧪 Tests

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### E2E Tests (Playwright)

```bash
cd frontend
npm run test:e2e
```

## 💡 Utilisation de l'Intelligence Temporelle

### Questions Temporelles Supportées

L'assistant peut maintenant répondre à des questions temporelles complexes :

```
"Cette livraison est-elle en retard ?"
→ Calcule le délai par rapport à la date actuelle et signale les retards

"Quelle est la tendance des ventes ?"
→ Analyse les variations mensuelles et identifie les patterns saisonniers

"Quel est le lead time moyen de mes fournisseurs ?"
→ Calcule automatiquement les délais entre commandes et livraisons

"Y a-t-il des commandes avec des délais anormaux ?"
→ Détecte les outliers (>2 écarts-types de la moyenne)
```

### Détection Automatique

Le système détecte automatiquement les colonnes de dates dans vos fichiers Excel/CSV :
- Colonnes nommées : `date_commande`, `date_livraison`, `order_date`, `delivery_date`, etc.
- Validation du format : Vérifie que les valeurs sont bien des dates valides
- Calcul des lead times : Si 2 colonnes temporelles détectées → calcul automatique des délais

### Configuration Manuelle

Si la détection automatique échoue, vous pouvez configurer manuellement :
1. Upload votre fichier
2. Accédez au panneau "Analyse Temporelle"
3. Sélectionnez les colonnes de dates pertinentes
4. Cliquez sur "Recalculer"

## 📚 Documentation

- **[PRD.md](./PRD.md)** - Spécifications fonctionnelles complètes
- **[ARCHITECTURE.md](./architecture.md)** - Analyse technique détaillée
- **[CLAUDE.md](./CLAUDE.md)** - Instructions pour le développement avec Claude Code
- **[API Documentation](http://localhost:8000/docs)** - Documentation interactive FastAPI

## 🛠️ Commandes Utiles

```bash
# Rebuild containers
docker-compose up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Access PostgreSQL
docker exec -it supply-chain-db psql -U supply_chain_user -d supply_chain_ai

# Access Redis CLI
docker exec -it supply-chain-redis redis-cli

# Run migrations manually
docker exec -it supply-chain-backend python -m alembic upgrade head

# Check running containers
docker-compose ps
```

## 📋 Roadmap

### Phase MVP (Actuelle) ✅
- Interface chat avec historique
- Streaming LLM
- Citations basiques
- Purge 24h

### Phase V1 (Prochaine)
- RAG avec TypeSense
- Upload de fichiers
- Citations Excel précises (cellule par cellule)
- Mode Alerte (détection d'incohérences)
- Double Persona (Opérationnel/Directeur)
- Export de rapports

### Phase V2
- Simulateur What-if
- Analyse multi-documents complexe
- Bibliothèque de frameworks Supply Chain

## 🤝 Contribution

Ce projet utilise [OpenSpec](./openspec/AGENTS.md) pour la gestion des changements et spécifications.

Pour contribuer:

1. Créer une proposition de changement: `/openspec:proposal <description>`
2. Obtenir l'approbation
3. Implémenter: `/openspec:apply <change-id>`

## 📄 Licence

Propriétaire - Tous droits réservés

## 📞 Support

Pour toute question ou problème, consulter la documentation ou créer une issue dans le repository.
