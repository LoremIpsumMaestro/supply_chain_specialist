# Tests E2E - Supply Chain AI Assistant

Tests End-to-End avec Playwright pour valider le fonctionnement complet de l'application.

## 📁 Structure

```
e2e/
├── fixtures/          # Fichiers de test (Excel, PDF, Word, etc.)
├── tests/            # Tests Playwright
│   ├── 01-basic-navigation.spec.ts
│   ├── 02-authentication.spec.ts
│   ├── 03-file-upload.spec.ts
│   ├── 04-rag-and-citations.spec.ts
│   ├── 05-temporal-intelligence.spec.ts
│   ├── 06-responsive-design.spec.ts
│   └── 07-data-purge.spec.ts
└── README.md         # Ce fichier
```

## 🚀 Installation

```bash
cd frontend

# Installer Playwright (déjà fait)
npm install -D @playwright/test

# Installer les navigateurs
npx playwright install
```

## 🧪 Exécution des Tests

### Tous les tests

```bash
npm run test:e2e
```

### Mode UI interactif (recommandé pour debug)

```bash
npm run test:e2e:ui
```

### Mode debug

```bash
npm run test:e2e:debug
```

### Tests spécifiques

```bash
# Un seul fichier
npx playwright test 03-file-upload

# Un seul test
npx playwright test -g "devrait permettre l'upload d'un fichier Excel"

# Par navigateur
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Par device
npx playwright test --project="Mobile Chrome"
npx playwright test --project="iPad"
```

### Rapport de tests

```bash
npm run test:e2e:report
```

## 📋 Tests Implémentés

### 1. Navigation de Base ✅
- Chargement de la page d'accueil
- Page de login
- Page d'inscription
- Redirection si non authentifié

### 2. Authentification ✅
- Inscription nouvel utilisateur
- Connexion avec bons identifiants
- Erreur avec mauvais identifiants

### 3. Upload et Parsing de Documents ✅
- Upload fichier Excel (.xlsx)
- Upload fichier CSV (.csv)
- Upload fichier Word (.docx)
- Upload fichier PowerPoint (.pptx)
- Upload fichier texte (.txt)
- Rejet fichier non supporté
- Rejet fichier trop volumineux
- Upload multiple de fichiers

### 4. RAG et Citations ✅
- Question sur les stocks avec citation Excel
- Citation cellule Excel précise (ex: "feuille 'Stocks', cellule B2")
- Question sur les commandes
- Question sur les fournisseurs
- Indication quand info non disponible
- Recherche multi-feuilles
- Citations cliquables
- Gestion de plusieurs documents

### 5. Intelligence Temporelle ✅
- Détection automatique colonnes de dates
- Calcul lead times automatiques
- Identification commandes en retard
- Comparaison avec date actuelle
- Statistiques temporelles (min, max, moyenne)
- Identification outliers dans lead times
- Questions sur saisonnalité
- Contexte temporel dans citations

### 6. Responsive Design ✅
- Desktop (1920x1080): interface complète, sidebar visible
- Tablette (768x1024): sidebar collapsible
- Mobile (375x667): sidebar cachée par défaut, boutons tactiles
- Tests de défilement
- Tests d'orientation (portrait/paysage)

### 7. Purge Automatique 24h ⚠️
- Information sur la purge automatique (conceptuel)
- Indicateur de temps restant (si implémenté)
- Suppression manuelle avant expiration
- Politique de rétention des données

**Note**: Les vrais tests de purge doivent être dans `backend/tests/test_purge.py`

## 📊 Couverture des Tests

| Fonctionnalité | Couverture | Statut |
|----------------|------------|--------|
| Navigation | 100% | ✅ |
| Authentification | 80% | ✅ |
| Upload Documents | 90% | ✅ |
| RAG & Citations | 85% | ✅ |
| Intelligence Temporelle | 80% | ✅ |
| Responsive | 90% | ✅ |
| Purge 24h | 30% (conceptuel) | ⚠️ |

## 🔧 Configuration

### playwright.config.ts

- **Timeout**: 60s par test
- **Retries**: 2 sur CI, 0 en local
- **Reporters**: HTML + List + JSON
- **Screenshots**: Sur échec uniquement
- **Vidéos**: Conservées sur échec
- **Navigateurs**: Chromium, Firefox, WebKit
- **Devices**: Desktop, iPad, Mobile (Chrome & Safari)

### Variables d'Environnement

```bash
# Backend URL (par défaut)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Frontend URL
BASE_URL=http://localhost:3000
```

## 🐛 Debug des Tests

### Playwright Inspector

```bash
npx playwright test --debug
```

### Traces

```bash
# Générer des traces
npx playwright test --trace on

# Voir les traces
npx playwright show-trace trace.zip
```

### Console Logs

Les tests affichent des logs console. Pour voir plus de détails :

```bash
DEBUG=pw:api npx playwright test
```

## 📝 Bonnes Pratiques

### 1. Locators
- Préférer `getByRole`, `getByLabel`, `getByText` aux sélecteurs CSS
- Utiliser `data-testid` pour les éléments sans rôle sémantique
- Éviter les sélecteurs CSS/XPath fragiles

### 2. Assertions
- Utiliser `expect().toBeVisible()` plutôt que `.toBeTruthy()`
- Ajouter des timeouts pour les éléments async
- Vérifier l'état, pas seulement la présence

### 3. Attentes
- Utiliser `waitForURL` pour les redirections
- `waitForTimeout` en dernier recours (préférer `waitForSelector`)
- Éviter les attentes arbitraires

### 4. Fixtures
- Utiliser des données réalistes
- Nettoyer après les tests (supprimer users test)
- Versionner les fichiers de test

## 🚨 Pré-requis pour les Tests

### Backend doit être démarré

```bash
# Docker
docker-compose up -d

# Ou développement local
cd backend
python -m backend.main
```

### Services requis

- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (port 9000)
- TypeSense (port 8108)
- Ollama (port 11434) - ou OpenAI/Anthropic API configurée
- Backend API (port 8000)
- Frontend (port 3000)

### Vérifier que tout fonctionne

```bash
# Backend health
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

## 📈 CI/CD

### GitHub Actions (exemple)

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Start services
        run: docker-compose up -d

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## 🔗 Ressources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-test)

## ❓ FAQ

### Les tests échouent localement

1. Vérifier que tous les services Docker sont démarrés
2. Vérifier les ports (3000, 8000, etc.)
3. Nettoyer les données de test (`docker-compose down -v`)

### Les tests sont lents

- Exécuter sur un seul navigateur: `--project=chromium`
- Désactiver les vidéos: `--video=off`
- Augmenter les workers: `--workers=4`

### Erreur "Target closed"

- Augmenter les timeouts dans `playwright.config.ts`
- Vérifier la stabilité du backend
- Vérifier les logs du navigateur

## 📞 Support

Pour toute question, voir le README principal ou créer une issue sur le repository.
