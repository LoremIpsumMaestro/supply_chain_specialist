# Spec Delta: RAG Integration

## MODIFIED Requirements

### Requirement: RAG Context Injection
The LLM service SHALL inject RAG context AND system date into all prompts for anti-hallucination and temporal awareness.

**Changes from original**: Added system date injection requirement.

#### Scenario: System date injected in prompt
- **WHEN** the LLM builds a system prompt for any query
- **THEN** the prompt SHALL include the current date in French format before RAG context
- **AND** use format: "DATE ACTUELLE: DD Month YYYY" (example: "DATE ACTUELLE: 29 janvier 2026")

#### Scenario: Combined temporal and RAG context
- **WHEN** a user asks "Are any deliveries late?"
- **AND** RAG retrieves chunks with delivery dates
- **THEN** the system prompt SHALL include:
  1. Current system date
  2. RAG context with document excerpts and dates
  3. Instructions to calculate delays using the current date

#### Scenario: No RAG results but date still injected
- **WHEN** a user asks a general question with no relevant RAG results
- **THEN** the system SHALL still inject the current date in the prompt
- **AND** the LLM can answer using general knowledge with temporal awareness

#### Scenario: Temporal context in RAG results
- **WHEN** RAG search returns chunks with `temporal_context` in metadata
- **THEN** the system SHALL include temporal metrics in the RAG context string
- **AND** format example: "[Source 1: sales.xlsx, cellule C12, date: 15 déc 2025, tendance: +25% vs mois précédent]"

---

### Requirement: Citation Extraction and Display
Citations SHALL include temporal context metadata when available.

**Changes from original**: Extended to include temporal metadata in citations.

#### Scenario: Citation with temporal context
- **WHEN** a search result includes `temporal_context` in metadata
- **THEN** the citation SHALL display the date and temporal metrics
- **AND** format example: "Selon la cellule C12 (feuille 'Ventes', fichier sales.xlsx, date: 15 décembre 2025): 150 unités (+25% vs novembre)"

#### Scenario: Citation without temporal context
- **WHEN** a PDF chunk has no temporal metadata
- **THEN** the citation SHALL use the original format without temporal info
- **AND** format example: "Selon la page 3 du fichier rapport.pdf: ..."
