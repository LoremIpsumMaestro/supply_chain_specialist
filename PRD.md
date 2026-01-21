# Spécifications Fonctionnelles : Assistant IA Supply Chain Spécialisé

## 1. Vision du Produit
Interface de chat type "ChatGPT" dédiée aux professionnels de la Supply Chain (Opérationnels et Directeurs). L'outil permet d'interagir avec des LLM pour analyser des contextes opérationnels et stratégiques à partir de documents fournis par l'utilisateur.

---

## 2. Principes Fondamentaux
- **Confidentialité Stricte :** Rétention des fichiers et des données vectorielles limitée à **24 heures**.
- **Fiabilité (Anti-hallucination) :** Utilisation d'un RAG (Retrieval Augmented Generation) ancré sur des documents utilisateurs et une base de connaissances métier.
- **Expertise métier :** Prise en compte de la temporalité, de la saisonnalité et du jargon Supply Chain.
- **Indépendance :** Pas de connexion directe aux SI (ERP/WMS) ou aux données de marché externes pour le moment.

---

## 3. Feuille de Route (Roadmap)

### PHASE 1 : MVP (Minimum Viable Product)
*Objectif : Sécurité, Lecture et Analyse de base.*

- **Interface & Sécurité :**
    - Chat UI fluide avec historique des conversations.
    - Logic de **purge automatique (Data & Index) après 24h**.
- **Moteur RAG & Formats :**
    - Support des formats : **Excel (.xlsx), CSV, PDF, Word, PowerPoint, Texte**.
    - Base de connaissances statique intégrée (concepts fondamentaux de la Supply Chain).
- **Fonctionnalités Clés :**
    - **Citations :** Affichage systématique des sources (ex: "Selon la cellule C12 du fichier X...").
    - **Mode Alerte :** Détection d'incohérences de base (stocks négatifs, dates incohérentes).
    - **Analyse de Contexte :** Répondre à des questions sur les documents fournis.

### PHASE 2 : V1 (Expertise Contextuelle)
*Objectif : Intelligence métier et exploitation des résultats.*

- **Intelligence Temporelle :**
    - Injection de la date système.
    - Analyse des tendances (saisonnalité, délais de livraison/Lead Times).
- **Double Persona :**
    - Mode **Opérationnel** (Focus : ruptures, exécution, alertes).
    - Mode **Directeur** (Focus : financier, stratégique, BFR, synthèse haute).
- **Sorties Structurées :**
    - Module d'exportation de rapports (Word/PDF) basés sur la discussion.
    - Extraction de données calculées en format structuré (CSV/JSON).
- **Comparaison de Scénarios :**
    - Analyse croisée entre deux fichiers (ex: Comparaison de deux plans de production).

### PHASE 3 : V2 (Simulation & Proactivité)
*Objectif : Aide à la décision avancée.*

- **Simulateur de Scénarios (Hypothèses) :**
    - Capacité de poser des questions "What-if" sans ré-uploader de fichiers (modification de variables en mémoire).
- **Analyse Multi-Documents complexe :**
    - Corrélation avancée entre de multiples sources (ex: Contrat transport VS Données de facturation).
- **Bibliothèque de Frameworks :**
    - Intégration de formules de calcul standard (Stock de sécurité, Point de commande, etc.).