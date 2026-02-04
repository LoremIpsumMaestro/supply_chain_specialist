# rag-integration Spec Delta

## MODIFIED Requirements

### Requirement: RAG Context Injection
The LLM service SHALL inject RAG context AND system date into all prompts for anti-hallucination and temporal awareness. Responses SHALL be formatted in markdown for improved readability.

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

#### Scenario: LLM encouraged to use markdown formatting
- **WHEN** the system prompt is built for any query
- **THEN** the prompt SHALL include formatting guidelines instructing the LLM to:
  - Use markdown tables for structured data presentation
  - Use bulleted or numbered lists for enumerations
  - Use code blocks with language specification for code/SQL examples
  - Use **bold** for important points and _italic_ for nuances
- **AND** the guidelines are added after the RAG context instructions

### Requirement: Citation Extraction and Display
Citations SHALL include temporal context metadata when available and be formatted to integrate well with markdown responses.

#### Scenario: Citation with temporal context
- **WHEN** a search result includes `temporal_context` in metadata
- **THEN** the citation SHALL display the date and temporal metrics
- **AND** format example: "Selon la cellule C12 (feuille 'Ventes', fichier sales.xlsx, date: 15 décembre 2025): 150 unités (+25% vs novembre)"

#### Scenario: Citation without temporal context
- **WHEN** a PDF chunk has no temporal metadata
- **THEN** the citation SHALL use the original format without temporal info
- **AND** format example: "Selon la page 3 du fichier rapport.pdf: ..."

#### Scenario: Citations in markdown-formatted responses
- **WHEN** the LLM generates a response with markdown formatting (e.g., tables, lists)
- **THEN** citations are integrated seamlessly within the markdown structure
- **AND** citations may appear as blockquotes (>) when appropriate
- **AND** citations maintain readability and do not break markdown rendering

## ADDED Requirements

### Requirement: Markdown Response Formatting
The LLM SHALL be instructed to generate responses using markdown syntax for improved readability and structure.

#### Scenario: Generate table for structured data
- **WHEN** the LLM generates a response presenting tabular data (e.g., inventory levels, delivery dates)
- **THEN** the response uses markdown table syntax
- **AND** the table has headers and properly formatted rows
- **AND** example format:
  ```
  | Produit | Stock | Statut |
  |---------|-------|--------|
  | Item A  | 150   | OK     |
  | Item B  | 5     | Alerte |
  ```

#### Scenario: Generate lists for enumerations
- **WHEN** the LLM generates a response with multiple items or action steps
- **THEN** the response uses bulleted lists (unordered) or numbered lists (ordered)
- **AND** nested lists have proper indentation
- **AND** example format:
  ```
  Actions recommandées:
  1. Vérifier les stocks suivants
  2. Commander immédiatement:
     - Item B (stock critique)
     - Item C (rupture prévue dans 3 jours)
  ```

#### Scenario: Generate code blocks for SQL/Python examples
- **WHEN** the LLM generates a response with code, SQL queries, or technical examples
- **THEN** the response uses fenced code blocks with language specification
- **AND** example format:
  ```
  ```sql
  SELECT * FROM inventory WHERE stock < 10
  ````
  ```

#### Scenario: Use inline formatting for emphasis
- **WHEN** the LLM generates a response needing emphasis
- **THEN** **bold** is used for critical information or warnings
- **AND** _italic_ is used for nuances or secondary information
- **AND** `inline code` is used for technical terms, variable names, or cell references

#### Scenario: Fallback to plain text for simple responses
- **WHEN** the LLM generates a simple yes/no answer or brief statement
- **THEN** markdown is not required
- **AND** the response remains concise without unnecessary formatting
