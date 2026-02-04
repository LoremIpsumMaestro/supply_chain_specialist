# Change: Révision du formatage des réponses en markdown

## Why
Actuellement, les réponses de l'assistant dans l'interface chat sont affichées en texte brut sans formatage markdown. Cela rend difficile la lecture de contenus structurés (tableaux, listes, blocs de code) générés par le LLM, dégradant l'expérience utilisateur pour les analyses Supply Chain qui nécessitent souvent de présenter des données tabulaires, des listes d'actions, ou des extraits de code.

## What Changes
- **Frontend**: Ajout d'une bibliothèque de rendu markdown (react-markdown + remark-gfh pour GitHub Flavored Markdown)
- **Frontend**: Création d'un composant MessageContent avec support complet du markdown (tables, listes, code blocks avec syntax highlighting, citations)
- **Frontend**: Application de styles cohérents avec le design system shadcn/ui pour le contenu markdown
- **Backend**: Ajustement des prompts LLM pour encourager l'utilisation de markdown dans les réponses
- **Specs**: Mise à jour des exigences d'affichage des messages pour inclure le rendu markdown

## Impact
- **Specs affectées**:
  - `chat-interface` (affichage des messages)
  - `rag-integration` (formatage des citations)
- **Code affecté**:
  - `frontend/components/chat/Message.tsx` (rendu des messages)
  - `frontend/package.json` (ajout dépendances)
  - `backend/services/llm_service.py` (prompts système)
- **Tests**: Mise à jour des tests E2E pour valider le rendu markdown
- **Dépendances**: Ajout de `react-markdown`, `remark-gfm`, `rehype-highlight` (conformément au principe "préférer les composants existants")

## Risks
- **Performance**: Le rendu markdown peut augmenter légèrement le temps de rendu des messages longs
  - Mitigation: Utilisation de react-markdown qui est optimisé pour React
- **Sécurité**: Injection de contenu malveillant via markdown
  - Mitigation: react-markdown échappe par défaut le HTML, pas de rendu HTML brut
- **Complexité**: Ajout de dépendances frontend
  - Mitigation: Bibliothèques mainstream et bien maintenues (react-markdown: 11M downloads/semaine)

## Non-Goals
- Mode sombre (hors scope MVP selon CLAUDE.md)
- Export des messages en markdown (fonctionnalité V1)
- Édition markdown côté utilisateur (hors scope)
