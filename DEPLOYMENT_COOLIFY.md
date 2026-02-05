# Déploiement Backend sur Coolify

Ce guide détaille le déploiement du backend FastAPI sur Coolify.

## 📋 Prérequis

- Un serveur VPS avec Ubuntu 22.04 ou 24.04 (Hetzner, DigitalOcean, OVH)
- Coolify installé sur le serveur
- Accès au repo GitHub

---

## 🚀 Étapes de Déploiement

### 1. Préparer le Serveur VPS

1. Créer un VPS chez un fournisseur (recommandé : Hetzner ~3€/mois)
   - OS : Ubuntu 22.04 LTS
   - Specs minimales : 2 vCPU, 4 GB RAM, 40 GB SSD

2. Se connecter au serveur via SSH :
   ```bash
   ssh root@VOTRE_IP_SERVEUR
   ```

### 2. Installer Coolify

Sur le serveur, exécuter :
```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Après installation, accéder à Coolify via :
```
http://VOTRE_IP_SERVEUR:8000
```

### 3. Configuration Coolify

#### A. Créer un nouveau projet

1. Se connecter à l'interface Coolify
2. Créer un nouveau projet : "Supply Chain Backend"
3. Ajouter une nouvelle application

#### B. Connecter le repo GitHub

1. Connecter votre compte GitHub
2. Sélectionner le repo : `supply_chain_specialist`
3. Choisir la branche : `main`
4. Définir le répertoire racine : `/backend`

#### C. Configurer l'application

**Type** : Dockerfile
**Dockerfile path** : `./Dockerfile`
**Port** : `8000`

### 4. Ajouter les Services

#### PostgreSQL
1. Ajouter un service PostgreSQL depuis Coolify
2. Nom : `supply-chain-db`
3. Version : PostgreSQL 16
4. Noter les credentials générés

#### Redis (Optionnel pour MVP)
1. Ajouter un service Redis
2. Nom : `supply-chain-redis`
3. Version : Redis 7

### 5. Variables d'Environnement

Dans Coolify, ajouter ces variables d'environnement :

```bash
# Database (utiliser l'URL PostgreSQL fournie par Coolify)
DATABASE_URL=postgresql://user:password@supply-chain-db:5432/dbname

# Redis (utiliser l'URL Redis fournie par Coolify)
REDIS_URL=redis://supply-chain-redis:6379

# CORS (ajouter l'URL de votre frontend Vercel)
CORS_ORIGINS=https://votre-frontend.vercel.app,http://localhost:3000

# JWT (générer une clé secrète forte)
JWT_SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire

# Services optionnels (désactiver pour MVP)
# TYPESENSE_HOST=localhost
# TYPESENSE_PORT=8108
# TYPESENSE_API_KEY=xyz123
# OLLAMA_HOST=http://localhost:11434
```

### 6. Déployer

1. Cliquer sur "Deploy"
2. Coolify va :
   - Cloner le repo
   - Builder l'image Docker
   - Démarrer le conteneur
   - Exposer l'application

3. Récupérer l'URL publique générée (ex: `https://your-app.coolify.io`)

---

## 🔧 Configuration Vercel

Une fois le backend déployé :

1. Aller sur Vercel Dashboard
2. Sélectionner votre projet frontend
3. Aller dans **Settings** → **Environment Variables**
4. Modifier/Ajouter :
   ```
   NEXT_PUBLIC_API_URL=https://votre-backend-url.coolify.io
   ```
5. Redéployer le frontend

---

## ✅ Vérification

Tester l'API déployée :

```bash
# Health check
curl https://votre-backend-url.coolify.io/health

# Réponse attendue
{"status":"healthy"}
```

---

## 📊 Monitoring

Dans Coolify, vous pouvez :
- Voir les logs en temps réel
- Monitorer l'utilisation CPU/RAM
- Configurer des alertes
- Voir les métriques de performance

---

## 🔄 Mise à Jour

Pour déployer une nouvelle version :
1. Pusher les changements sur GitHub
2. Coolify détecte automatiquement et redéploie
   OU
3. Redéployer manuellement depuis l'interface Coolify

---

## 🆘 Troubleshooting

### Erreur de connexion à la base de données
Vérifier que :
- PostgreSQL est bien démarré dans Coolify
- La variable `DATABASE_URL` est correcte
- Le réseau Docker permet la communication

### CORS Error
Vérifier que :
- L'URL Vercel est bien dans `CORS_ORIGINS`
- Pas d'espace dans la liste des origins
- Format : `https://app.vercel.app,https://autre-url.com`

### Logs
Accéder aux logs dans Coolify :
1. Aller dans l'application
2. Cliquer sur "Logs"
3. Voir les erreurs en temps réel
