# Guide de Démarrage Rapide

## 🚀 Lancer l'application en 5 minutes

### Prérequis

Vérifier que vous avez installé:
```bash
docker --version  # Docker 20+
docker-compose --version  # Docker Compose 2+
```

### Étape 1: Configuration des Variables d'Environnement

```bash
# Copier le fichier d'exemple
cp .env.example .env.local

# Éditer .env.local avec vos clés API
# Minimum requis: une des deux clés LLM
nano .env.local
```

Configurer au minimum:
```env
# Au moins une des deux clés API
OPENAI_API_KEY=sk-...
# OU
ANTHROPIC_API_KEY=sk-ant-...

# Générer une clé secrète aléatoire pour JWT
JWT_SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire

# Les autres variables sont déjà configurées pour Docker
```

### Étape 2: Lancer l'Application

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier que tout tourne
docker-compose ps
```

Vous devriez voir:
```
supply-chain-db        running
supply-chain-redis     running
supply-chain-backend   running
supply-chain-frontend  running
```

### Étape 3: Accéder à l'Application

Ouvrir votre navigateur:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Étape 4: Tester

1. Ouvrir http://localhost:3000
2. Vous devriez voir l'interface de chat
3. Cliquer sur "Nouvelle conversation"
4. Taper un message: "Bonjour, qui es-tu ?"
5. Voir la réponse streamer en temps réel

## 🔍 Vérification

### Vérifier les logs

```bash
# Tous les services
docker-compose logs -f

# Backend uniquement
docker-compose logs -f backend

# Frontend uniquement
docker-compose logs -f frontend
```

### Vérifier la base de données

```bash
# Se connecter à PostgreSQL
docker exec -it supply-chain-db psql -U supply_chain_user -d supply_chain_ai

# Lister les tables
\dt

# Voir les conversations
SELECT * FROM conversations;

# Quitter
\q
```

### Vérifier Redis

```bash
# Se connecter à Redis
docker exec -it supply-chain-redis redis-cli

# Ping
ping

# Quitter
exit
```

## ⚠️ Troubleshooting

### Problème: Les containers ne démarrent pas

```bash
# Vérifier les erreurs
docker-compose logs

# Rebuild les images
docker-compose up --build
```

### Problème: Port déjà utilisé

Si un port est déjà utilisé (3000, 8000, 5432, 6379):

```bash
# Option 1: Arrêter le service qui utilise le port
lsof -ti:3000 | xargs kill -9

# Option 2: Modifier docker-compose.yml pour utiliser d'autres ports
```

### Problème: Database connection error

```bash
# Vérifier que PostgreSQL est prêt
docker-compose logs postgres

# Attendre que le healthcheck passe
docker-compose ps
```

### Problème: Frontend ne peut pas joindre le backend

Vérifier que `NEXT_PUBLIC_API_URL` dans `.env.local` pointe vers le bon endpoint:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Problème: LLM streaming ne fonctionne pas

1. Vérifier que la clé API est valide
2. Vérifier les logs backend: `docker-compose logs -f backend`
3. Tester l'API directement: http://localhost:8000/docs

## 🛠️ Développement Local (sans Docker)

### Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer la DB (PostgreSQL doit tourner)
psql -U supply_chain_user -d supply_chain_ai -f db/migrations/001_create_conversations_and_messages.sql
psql -U supply_chain_user -d supply_chain_ai -f db/migrations/002_setup_purge_job.sql

# Lancer le serveur
python -m backend.main
```

### Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de dev
npm run dev
```

## 📝 Commandes Utiles

```bash
# Arrêter les services
docker-compose down

# Arrêter et supprimer les volumes (⚠️ supprime les données)
docker-compose down -v

# Rebuild après modification du code
docker-compose up --build

# Voir les logs en temps réel
docker-compose logs -f

# Redémarrer un service
docker-compose restart backend

# Accéder au shell d'un container
docker exec -it supply-chain-backend bash
```

## 🎯 Étapes Suivantes

1. ✅ Application lancée
2. Tester toutes les fonctionnalités
3. Uploader des documents (quand V1 sera implémenté)
4. Configurer le monitoring
5. Déployer en production

## 📚 Ressources

- [README.md](./README.md) - Documentation complète
- [PRD.md](./PRD.md) - Spécifications produit
- [ARCHITECTURE.md](./architecture.md) - Détails techniques
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Résumé implémentation

## 🆘 Support

En cas de problème:
1. Vérifier les logs: `docker-compose logs`
2. Vérifier que tous les services sont healthy: `docker-compose ps`
3. Consulter la documentation dans README.md
4. Créer une issue dans le repository

---

**Bon développement ! 🚀**
