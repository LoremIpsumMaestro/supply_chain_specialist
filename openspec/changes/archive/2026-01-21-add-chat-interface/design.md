# Design: Chat Interface with Conversation History

## Context
This is the foundational user interface for the Supply Chain AI Assistant MVP. The chat interface must provide a familiar, responsive experience similar to ChatGPT while supporting specialized features like document upload, precise citations (especially for Excel cells), and strict 24-hour data retention.

**Key Constraints:**
- Must support streaming LLM responses for perceived performance
- Citations must be inline and visually distinct
- All data (conversations, messages, files) must be purged after 24 hours
- Must work on desktop, tablet, and mobile devices
- No dark mode for MVP (per CLAUDE.md guidelines)

**Stakeholders:**
- Supply Chain Operators: Need quick access to operational data and alerts
- Supply Chain Directors: Focus on strategic insights and reports
- Development Team: Must maintain code quality and extensibility for V1/V2 phases

## Goals / Non-Goals

**Goals:**
- Provide a fluent, responsive chat interface for document analysis
- Persist conversation history with automatic 24-hour purge
- Support file upload with validation and progress indication
- Display citations inline with clear source attribution
- Enable conversation management (create, delete, switch, retrieve)
- Responsive design for desktop, tablet, and mobile
- Streaming responses for better UX

**Non-Goals:**
- Dark mode (deferred post-MVP per CLAUDE.md)
- Real-time collaboration or multi-user conversations
- Export/import of conversations
- Advanced formatting (markdown rendering can be basic)
- Conversation search (can be added in V1)
- Voice input/output

## Decisions

### Decision 1: Frontend Framework - Next.js 15 + shadcn/ui
**Choice:** Use Next.js 15 App Router with React Server Components and shadcn/ui for UI components.

**Rationale:**
- Aligns with project.md tech stack (Next.js 15 + React + TailwindCSS + shadcn/ui)
- shadcn/ui provides accessible, customizable components (per CLAUDE.md: "Préférer les composants existants")
- App Router enables hybrid rendering (RSC for conversation list, client components for chat)
- Strong TypeScript support and type safety
- Vercel deployment synergy

**Alternatives considered:**
- Plain React SPA: Worse SEO, more complex routing
- Remix: Less mature ecosystem, smaller community
- Vue/Nuxt: Team expertise is in React ecosystem

### Decision 2: State Management - Zustand
**Choice:** Use Zustand for client-side state management.

**Rationale:**
- Lightweight and simple (aligns with project.md conventions)
- Better performance than Context API for frequent updates
- Easy to integrate with React hooks
- Minimal boilerplate compared to Redux
- Project.md explicitly lists Zustand in tech stack

**Alternatives considered:**
- React Context: Performance issues with frequent chat updates
- Redux Toolkit: Overkill for MVP scope
- Jotai/Recoil: Less mature, smaller ecosystem

### Decision 3: Streaming Implementation - Vercel AI SDK
**Choice:** Use Vercel AI SDK (`@vercel/ai`) for LLM streaming.

**Rationale:**
- Project.md explicitly lists "@vercel/ai (streaming support)" in tech stack
- Built-in support for OpenAI and Anthropic streaming
- React hooks (`useChat`) simplify streaming implementation
- Handles backpressure and error recovery
- Well-maintained and documented

**Alternatives considered:**
- Manual SSE: More complexity, reinventing the wheel
- WebSockets: Overkill for unidirectional streaming
- Polling: Poor UX, increased latency

### Decision 4: Database Schema - PostgreSQL with separate tables
**Choice:** Create `conversations` and `messages` tables with foreign key relationship.

**Schema:**
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours')
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  citations JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_expires_at ON conversations(expires_at);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
```

**Rationale:**
- Separate tables allow efficient querying (list conversations without loading all messages)
- `expires_at` column enables pg_cron-based purge (per project.md)
- JSONB for citations allows flexible structure (Excel vs PDF citations differ)
- Indexes optimize common queries (user's conversations, expired data, conversation messages)
- Cascading deletes ensure data consistency

**Alternatives considered:**
- Single denormalized table: Poor query performance, data redundancy
- NoSQL (MongoDB): Less familiar to team, weaker consistency guarantees
- Embedding all messages in conversation JSONB: Query performance issues, size limits

### Decision 5: Citation Format - Inline with metadata badges
**Choice:** Display citations as inline badges/chips with metadata tooltip.

**Visual Design:**
```
Assistant: Le stock actuel est de 150 unités [📄 production.xlsx | Stocks | C12]
                                                 └─ clickable badge with tooltip
```

**Rationale:**
- Inline placement maintains reading flow
- Visual distinction (icon + colored badge) draws attention to sources
- Tooltip can show full metadata without cluttering main text
- Aligns with RAG anti-hallucination requirement (project.md: "Citations obligatoires")
- Excel citations show filename, sheet, cell as required (project.md: "Granularité: Accès cellule par cellule")

**Alternatives considered:**
- Footnotes: Interrupts reading flow, requires scrolling
- Sidebar: Hidden on mobile, distracts from main content
- Plain text: Harder to distinguish, not visually appealing

### Decision 6: File Upload - react-dropzone with progress
**Choice:** Use react-dropzone for drag-and-drop and file picker, with progress bar.

**Rationale:**
- Project.md explicitly lists "react-dropzone" in tech stack
- Accessible and keyboard-navigable
- Built-in file type and size validation
- Drag-and-drop improves UX
- Customizable styling with TailwindCSS

**Implementation:**
- Max file size: 50MB (per project.md: "Support fichiers jusqu'à 50MB (Phase MVP)")
- Allowed types: .xlsx, .csv, .pdf, .docx, .pptx, .txt
- Progress indication during upload and processing
- Visual confirmation when indexing completes

**Alternatives considered:**
- Native file input: Poor UX, no drag-and-drop
- Custom implementation: Reinventing the wheel, accessibility issues

### Decision 7: Auto-scroll Strategy - Scroll on new content with user override
**Choice:** Auto-scroll to bottom when new messages arrive, unless user has scrolled up.

**Behavior:**
- Default: Auto-scroll to bottom when user sends message or assistant responds
- User scrolls up: Disable auto-scroll, show "New message" pill at bottom
- Click pill: Re-enable auto-scroll and scroll to bottom
- Streaming: Continuously scroll to keep streaming text visible

**Rationale:**
- Matches user expectations from ChatGPT and other chat apps
- Respects user intent when reviewing previous messages
- Streaming auto-scroll maintains context visibility
- "New message" pill provides clear affordance to return to latest

**Alternatives considered:**
- Always auto-scroll: Annoying when reviewing history
- Never auto-scroll: User must manually scroll for every message
- Threshold-based (scroll if within X pixels): Unpredictable behavior

### Decision 8: Responsive Breakpoints - Mobile-first with sidebar toggle
**Choice:** Use TailwindCSS default breakpoints with collapsible sidebar on mobile.

**Breakpoints:**
- Mobile: < 768px → Sidebar hidden behind hamburger menu, full-width chat
- Tablet: 768px - 1024px → Sidebar toggle button, chat adapts width
- Desktop: > 1024px → Persistent sidebar, main chat area

**Rationale:**
- Aligns with TailwindCSS conventions (sm, md, lg, xl)
- Mobile-first approach ensures core functionality works on smallest screens
- Hamburger menu is familiar UI pattern for mobile navigation
- Desktop layout maximizes screen real estate for chat and sidebar

**Alternatives considered:**
- Bottom tab bar on mobile: Takes vertical space, conflicts with keyboard
- Always visible sidebar on tablet: Cramped chat area
- Single column on all devices: Poor use of desktop space

### Decision 9: API Architecture - REST with WebSocket for streaming
**Choice:** Use REST endpoints for CRUD operations, Server-Sent Events (SSE) for streaming.

**Endpoints:**
```
GET    /api/conversations          → List user's conversations
POST   /api/conversations          → Create new conversation
GET    /api/conversations/:id      → Get conversation with messages
DELETE /api/conversations/:id      → Delete conversation
POST   /api/conversations/:id/messages → Send message (returns SSE stream)
POST   /api/files                  → Upload file
```

**Rationale:**
- REST is simple and well-understood
- SSE (via Vercel AI SDK) handles streaming efficiently
- No need for bidirectional communication (WebSocket overkill)
- FastAPI backend supports both REST and SSE easily
- Aligns with project.md: "API: REST + WebSocket streaming"

**Alternatives considered:**
- GraphQL: Overkill for MVP, adds complexity
- tRPC: Python backend makes tRPC unavailable (TypeScript only)
- Pure WebSockets: More complex, requires connection management

## Risks / Trade-offs

### Risk 1: Streaming latency on slow connections
**Risk:** Users on slow networks may experience delayed streaming responses.

**Mitigation:**
- Implement request timeout (30s) with clear error message
- Show "generating response" indicator immediately
- Use smaller LLM model (gpt-3.5-turbo) as fallback if latency detected
- Monitor in V1 and consider adaptive model selection

### Risk 2: 24-hour purge complexity
**Risk:** Ensuring reliable 24-hour purge across conversations, messages, files, and vector indexes.

**Mitigation:**
- Use pg_cron for PostgreSQL purge (per project.md)
- TypeSense native TTL (86400s) for vector indexes (per project.md)
- MinIO TTL for file storage (per project.md)
- Add monitoring/alerting for purge failures in V1
- Manual purge API endpoint for emergency cleanup

### Risk 3: Citation accuracy with complex documents
**Risk:** Extracting precise cell references from Excel or page numbers from PDFs may fail.

**Mitigation:**
- Use openpyxl for Excel to get exact cell coordinates (per project.md)
- Test parser thoroughly with varied document structures
- Fallback to filename only if precise location cannot be determined
- Log citation extraction failures for debugging

### Risk 4: Mobile keyboard obscuring input
**Risk:** On mobile, soft keyboard may cover the input field.

**Mitigation:**
- Use `viewport` meta tag to prevent zooming
- Position input with `position: sticky` or viewport units
- Test on iOS Safari, Android Chrome
- Listen to `visualViewport` resize events to adjust layout

### Risk 5: Performance with long conversations
**Risk:** Loading conversations with hundreds of messages may be slow.

**Mitigation:**
- Implement pagination (load last 50 messages initially)
- "Load more" button to fetch older messages
- Virtual scrolling for very long conversations (defer to V1 if needed)
- Monitor message count in analytics

## Migration Plan

**Phase 1: Backend Setup (Days 1-2)**
1. Create database schema (conversations, messages tables)
2. Implement FastAPI endpoints (CRUD + streaming)
3. Setup pg_cron for 24-hour purge
4. Write tests for API endpoints

**Phase 2: Frontend Core (Days 3-5)**
1. Create Next.js pages and routing
2. Build chat UI components (MessageList, MessageInput, Sidebar)
3. Integrate Zustand for state management
4. Connect to backend API with fetch/axios

**Phase 3: Streaming & Citations (Days 6-7)**
1. Integrate Vercel AI SDK for streaming
2. Implement citation display with inline badges
3. Test streaming performance and error handling

**Phase 4: File Upload (Day 8)**
1. Add react-dropzone component
2. Implement file validation and upload
3. Show upload progress and confirmation

**Phase 5: Responsive & Polish (Days 9-10)**
1. Implement responsive breakpoints
2. Add auto-scroll behavior
3. Mobile testing and fixes
4. Accessibility improvements (ARIA labels, keyboard navigation)

**Rollback Strategy:**
- Database migrations are reversible (down migrations)
- Feature flags for gradual rollout (if needed in V1)
- No data migration needed (net-new feature)

**Testing Requirements:**
- Unit tests: React components, API endpoints
- Integration tests: End-to-end chat flow, file upload
- E2E tests: Playwright tests for full user journey (per CLAUDE.md)
- Performance tests: Streaming latency, large conversation loading
- Accessibility tests: WCAG 2.1 AA compliance

## Open Questions

1. **Conversation titles:** Auto-generate from first message or require user input?
   - **Recommendation:** Auto-generate using first 50 chars of first user message. Allow rename in V1.

2. **Message edit/delete:** Should users be able to edit or delete individual messages?
   - **Recommendation:** No for MVP. Conversations are immutable (simpler). Add in V1 if user feedback requests it.

3. **Offline support:** Should the chat work offline with cached conversations?
   - **Recommendation:** No for MVP. Requires service worker and complex sync logic. Defer to V2.

4. **Rate limiting:** How to handle users sending too many messages?
   - **Recommendation:** Backend rate limiting (10 messages/minute per user). Show friendly error message. Expand in V1 based on usage patterns.

5. **Message reactions:** Should users be able to react (thumbs up/down) to assistant messages?
   - **Recommendation:** No for MVP. Add feedback mechanism in V1 for model training.
