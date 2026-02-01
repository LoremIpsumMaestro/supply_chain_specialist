# Change: Add Temporal Intelligence to Supply Chain Assistant

## Why

Les professionnels Supply Chain travaillent avec des données intrinsèquement temporelles : commandes, livraisons, stocks, prévisions. Sans contexte temporel, le LLM ne peut pas :
- Identifier si des données sont récentes ou obsolètes
- Calculer des délais (lead times, retards)
- Détecter des tendances saisonnières (pics de ventes en décembre, creux en août)
- Comprendre le contexte d'urgence (commande en retard de 3 semaines vs 2 jours)

Cette fonctionnalité est **critique** pour passer d'un assistant "lecture de documents" à un véritable outil d'analyse métier. Elle correspond à la **Phase V1** du PRD (Intelligence Temporelle).

## What Changes

- **Injection date système** : Ajouter la date actuelle (format français : "29 janvier 2026") dans tous les prompts système du LLM
- **Détection colonnes temporelles** : Identifier automatiquement les colonnes de dates dans Excel/CSV (heuristiques + patterns courants)
- **Calcul lead times** : Calculer automatiquement les délais entre dates (commande → livraison) et détecter les retards
- **Analyse de tendances** : Extraire séries temporelles et calculer moyennes glissantes, variations, saisonnalité
- **Metadata enrichissement** : Ajouter `upload_date`, `detected_time_columns`, `time_range` aux métadonnées des chunks
- **API configuration** : Permettre à l'utilisateur de spécifier manuellement les colonnes de dates si la détection échoue

## Impact

### Affected specs
- **temporal-analysis** (NEW): Nouvelle capability pour l'analyse temporelle
- **rag-integration** (MODIFIED): Injection date système dans prompts
- **document-processing** (MODIFIED): Détection colonnes temporelles + enrichissement métadonnées

### Affected code
- `backend/services/llm_service.py` : Injection date système dans `_build_messages()`
- `backend/services/document_parser.py` : Détection colonnes dates dans `ExcelParser`, `CSVParser`
- `backend/services/temporal_service.py` (NEW): Service pour analyse temporelle
- `backend/api/files.py` : Endpoint configuration colonnes temporelles
- `backend/models/file.py` : Ajout champs `temporal_metadata`
- Frontend : UI pour configuration manuelle colonnes (optionnel, si heuristique échoue)

### Breaking Changes
**Aucun** : Toutes les modifications sont additives et rétro-compatibles.

### Performance Considerations
- Détection colonnes temporelles : +100-200ms par fichier Excel/CSV (acceptable)
- Calculs tendances : +50-100ms par requête avec séries temporelles (acceptable)
- Pas d'impact sur latence streaming LLM (injection date = <10ms)

## Success Criteria

✅ La date système est visible dans toutes les réponses contextuelles du LLM

✅ Pour un fichier Excel avec colonnes `date_commande` et `date_livraison`, le système calcule automatiquement les lead times

✅ Pour un CSV avec ventes mensuelles sur 12 mois, le système détecte une saisonnalité (ex: pic en décembre)

✅ Si la détection heuristique échoue, l'utilisateur peut manuellement spécifier les colonnes de dates

✅ Les réponses du LLM mentionnent explicitement les délais calculés (ex: "Cette commande a un retard de 15 jours par rapport à la date prévue")

## Migration Path

Aucune migration nécessaire : les fichiers déjà uploadés continuent de fonctionner. La nouvelle fonctionnalité s'active automatiquement pour les nouveaux uploads.

## Open Questions

- [ ] Faut-il supporter les fuseaux horaires (UTC vs local) pour la date système ? **Réponse recommandée**: Non pour MVP, toujours UTC.
- [ ] Faut-il calculer en jours calendaires ou jours ouvrés ? **Réponse recommandée**: Jours calendaires pour MVP, jours ouvrés en V2.
- [ ] Quelle taille minimale de série temporelle pour détecter saisonnalité ? **Réponse recommandée**: Minimum 6 mois (2 saisons).
