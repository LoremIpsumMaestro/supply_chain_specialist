<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

---

## Aperçu du Projet

### Objectif
Assistant IA Supply Chain spécialisé permettant aux professionnels (Opérationnels et Directeurs) d'analyser leurs données et contextes opérationnels via une interface de chat type "ChatGPT". L'outil exploite un RAG (Retrieval Augmented Generation) pour fournir des analyses fiables et sourcées à partir de documents utilisateurs.

### Architecture Globale
- **Frontend**: Next.js 15 + React + TailwindCSS + shadcn/ui
- **Backend**: FastAPI (Python)
- **LLM**: OpenAI API / Anthropic Claude API
- **RAG**: LangChain + TypeSense (self-hosted)
- **Document Processing**: pandas + openpyxl + PyPDF2 + python-docx + python-pptx
- **Storage**: PostgreSQL + Redis (TTL)
- **Scheduling**: Celery + Redis
- **Déploiement**: Docker + AWS/GCP

---

## Style Visuel

- Interface claire et minimaliste
- **Pas de mode sombre pour le MVP**
- Design orienté professionnels Supply Chain
- Utiliser shadcn/ui + TailwindCSS pour la cohérence visuelle

---

## Contraintes et Politiques

### Sécurité
- ⚠️ **NE JAMAIS exposer les clés API au client**
- Toutes les clés API (OpenAI, Anthropic, TypeSense, etc.) doivent rester côté backend
- Utiliser des variables d'environnement (.env) pour les secrets
- Purge automatique des données et index vectoriels après 24h (confidentialité stricte)

### Dépendances
- **Préférer les composants existants** (shadcn/ui) plutôt que d'ajouter de nouvelles bibliothèques UI
- Minimiser les dépendances pour réduire la complexité et la surface d'attaque
- Privilégier les solutions natives quand possible

---

## Tests d'Interface

À la fin de chaque développement impliquant l'interface graphique :

1. **Tester avec playwright-skill**
2. Vérifier que l'interface est :
   - **Responsive** (mobile, tablette, desktop)
   - **Fonctionnelle** (tous les éléments interactifs fonctionnent)
   - **Conforme au besoin développé** (répond aux spécifications)

Exemple de commande :
```bash
# Lancer les tests Playwright
npm run test:e2e
```

---

## Documentation

### Documents de Référence

- **[PRD (Product Requirements Document)](./PRD.md)** : Spécifications fonctionnelles complètes, roadmap, et principes fondamentaux
- **[ARCHITECTURE](./ARCHITECTURE.md)** : Analyse technique détaillée, comparaison des stacks, et choix technologiques

### Consulter la Documentation
Toujours se référer à ces documents avant toute implémentation majeure pour s'assurer de l'alignement avec la vision produit et l'architecture technique.

---

## Context7 - Documentation de Bibliothèques

**Utilisation automatique obligatoire** : Utilise toujours Context7 lorsque tu as besoin de :
- Génération de code
- Étapes de configuration ou d'installation
- Documentation de bibliothèque/API

Cela signifie que tu dois **automatiquement utiliser les outils MCP Context7** pour :
1. Résoudre l'identifiant de bibliothèque (`resolve-library-id`)
2. Obtenir la documentation de bibliothèque (`query-docs`)

**Sans que j'aie à le demander explicitement.**

### Exemples d'Utilisation

```python
# Avant d'utiliser LangChain
# → Appeler Context7 pour obtenir la doc LangChain à jour

# Avant d'utiliser TypeSense
# → Appeler Context7 pour obtenir la doc TypeSense à jour

# Avant d'utiliser FastAPI
# → Appeler Context7 pour obtenir la doc FastAPI à jour
```

### Bibliothèques Principales du Projet

- **Backend**: FastAPI, LangChain, TypeSense, pandas, openpyxl
- **Frontend**: Next.js, React, TailwindCSS, shadcn/ui
- **LLM**: OpenAI API, Anthropic Claude API
- **Storage**: PostgreSQL, Redis
- **Task Queue**: Celery