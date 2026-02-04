# Design: Markdown Rendering in Chat Interface

## Context
The current implementation displays LLM responses as plain text using `whitespace-pre-wrap`. While this preserves line breaks, it doesn't support rich formatting like tables, code blocks, or lists that are essential for Supply Chain analysis (data tables, KPI lists, SQL/Python snippets).

**Constraints:**
- Must maintain streaming message support
- Must be compatible with shadcn/ui design system
- Must not introduce security vulnerabilities (XSS)
- Must work on mobile/tablet/desktop (responsive)
- Must follow CLAUDE.md constraint: "Préférer les composants existants plutôt que d'ajouter de nouvelles bibliothèques UI" → use mainstream, well-maintained libraries

**Stakeholders:**
- End users: Supply Chain professionals needing structured data display
- Developers: Need to maintain consistency with existing UI components

## Goals / Non-Goals

### Goals
- Render markdown in assistant messages (tables, lists, code blocks, blockquotes)
- Support GitHub Flavored Markdown for enhanced table support
- Maintain streaming message rendering performance
- Integrate seamlessly with existing shadcn/ui styling
- Ensure security (no arbitrary HTML injection)

### Non-Goals
- User-side markdown editing (out of scope)
- Markdown in user messages (display as-is for now)
- Export to markdown files (deferred to V1)
- Dark mode support (MVP constraint in CLAUDE.md)

## Decisions

### Decision 1: Use react-markdown + remark-gfm + rehype-highlight

**Why:**
- **react-markdown**: Industry standard (11M+ weekly downloads), actively maintained, secure by default (escapes HTML)
- **remark-gfm**: Official plugin for GitHub Flavored Markdown (tables, strikethrough, task lists)
- **rehype-highlight**: Syntax highlighting for code blocks using highlight.js under the hood

**Alternatives considered:**
1. **markdown-to-jsx**: Lighter weight but less feature-rich, no official GFM support
   - Rejected: Missing table support, less ecosystem
2. **marked + custom renderer**: More control but requires more maintenance
   - Rejected: Overkill for MVP needs, security concerns with custom rendering
3. **No markdown library, manual parsing**: Maximum control
   - Rejected: Too much complexity, reinventing the wheel

**Trade-offs:**
- Bundle size increase: ~50KB gzipped (acceptable for enhanced UX)
- Dependency on external library: Mitigated by using mainstream library with strong maintenance

### Decision 2: Apply markdown rendering only to assistant messages

**Why:**
- User messages are typically short questions/commands, don't need markdown
- Keeps implementation simpler
- Avoids confusion if user accidentally uses markdown syntax

**Alternatives considered:**
- Render markdown for both user and assistant: Could be confusing if user doesn't expect markdown to render
  - Rejected: Simpler UX to keep user messages as plain text

### Decision 3: Custom styles using Tailwind + shadcn/ui tokens

**Why:**
- Consistent with existing design system
- No need for external CSS framework
- Leverage existing color/spacing/typography variables

**Implementation approach:**
```tsx
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  rehypePlugins={[rehypeHighlight]}
  components={{
    table: ({children}) => <table className="border-collapse border border-gray-300 my-4">{children}</table>,
    th: ({children}) => <th className="border border-gray-300 px-4 py-2 bg-gray-50">{children}</th>,
    td: ({children}) => <td className="border border-gray-300 px-4 py-2">{children}</td>,
    code: ({inline, children}) => inline
      ? <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">{children}</code>
      : <code className="block bg-gray-900 text-gray-100 p-4 rounded my-2">{children}</code>,
    // ... more component overrides
  }}
>
  {content}
</ReactMarkdown>
```

### Decision 4: Backend prompt engineering for markdown

**Update system prompt to include:**
```python
system_content += (
    "\n\nFORMATAGE DES RÉPONSES:\n"
    "- Utilise des tableaux markdown pour présenter des données structurées\n"
    "- Utilise des listes à puces ou numérotées pour les énumérations\n"
    "- Utilise des blocs de code avec ```language pour les exemples de code/SQL\n"
    "- Utilise **gras** pour les points importants, _italique_ pour les nuances\n"
)
```

**Why:**
- Guides LLM to produce well-formatted output
- Improves readability without changing core RAG logic

## Risks / Trade-offs

### Risk 1: XSS via markdown injection
**Mitigation:**
- react-markdown escapes HTML by default (`allowDangerousHtml: false`)
- Don't enable `rehype-raw` plugin (which would allow HTML passthrough)
- Validate: Add test with malicious markdown input

### Risk 2: Performance degradation with large messages
**Mitigation:**
- react-markdown is optimized for React reconciliation
- Test with realistic large messages (e.g., 50-row tables)
- If needed, add virtualization for very long message lists (deferred)

### Risk 3: Streaming UX disruption
**Mitigation:**
- Markdown rendering works with partial content (graceful degradation)
- Test streaming specifically with incomplete markdown (e.g., partial table)

### Risk 4: Responsive table overflow on mobile
**Mitigation:**
- Wrap tables in `<div className="overflow-x-auto">` for horizontal scroll
- Test on mobile viewport (<768px) in E2E tests

## Migration Plan

### Phase 1: Frontend Implementation (Non-breaking)
1. Install dependencies
2. Create MessageContent component
3. Update Message.tsx to use MessageContent for assistant messages only
4. Test with existing messages (should display identically if no markdown)

### Phase 2: Backend Prompt Update
1. Update system prompt in llm_service.py
2. Deploy backend
3. Monitor LLM response quality

### Phase 3: Validation
1. Run E2E tests with markdown content
2. Manual testing with real Supply Chain data (Excel tables → LLM markdown tables)
3. Rollback plan: Revert Message.tsx to use plain text rendering

### Rollback
If critical issues arise:
1. Revert `Message.tsx` to previous version (whitespace-pre-wrap)
2. Keep dependencies installed for future retry
3. Investigate root cause

## Open Questions
- Should we add a "Copy as Markdown" button for assistant messages? (Deferred to V1)
- Should we render citations as markdown links? (Requires backend change to include URLs)
  - **Decision for MVP**: Keep current citation format, enhance in V1 if needed
