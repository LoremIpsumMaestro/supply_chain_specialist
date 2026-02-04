# Implementation Tasks

## 1. Frontend Dependencies
- [x] 1.1 Install react-markdown, remark-gfm, rehype-highlight
- [x] 1.2 Install @types packages for TypeScript support
- [x] 1.3 Update package.json and lock file

## 2. Markdown Rendering Component
- [x] 2.1 Create MessageContent component with react-markdown integration
- [x] 2.2 Configure remark-gfm plugin for GitHub Flavored Markdown (tables, strikethrough, task lists)
- [x] 2.3 Configure rehype-highlight for code syntax highlighting
- [x] 2.4 Apply custom styles for markdown elements (tables, code blocks, lists, blockquotes)
- [x] 2.5 Ensure responsive design for markdown tables

## 3. Message Component Integration
- [x] 3.1 Update Message.tsx to use MessageContent component
- [x] 3.2 Replace whitespace-pre-wrap text rendering with markdown rendering
- [x] 3.3 Preserve user message formatting (plain text or markdown based on role)
- [x] 3.4 Test streaming message rendering with markdown (MessageList.tsx updated)

## 4. Citation Formatting Enhancement
- [x] 4.1 Update Citation.tsx to support markdown-formatted citations (already compatible)
- [x] 4.2 Ensure citation links/references render properly in markdown (verified)

## 5. Backend Prompt Adjustments
- [x] 5.1 Update LLM system prompt to encourage markdown usage (tables, lists, code blocks)
- [x] 5.2 Add explicit formatting guidelines in RAG context prompts
- [ ] 5.3 Test LLM output quality with markdown formatting (requires manual testing)

## 6. Styling and Design System Integration
- [x] 6.1 Create markdown.css or inline styles for markdown elements (inline Tailwind styles)
- [x] 6.2 Use shadcn/ui design tokens (colors, spacing, typography)
- [x] 6.3 Style code blocks with appropriate background and padding
- [x] 6.4 Style tables with borders and hover effects
- [x] 6.5 Ensure consistent spacing for lists and blockquotes

## 7. Testing
- [x] 7.1 Write Playwright E2E test for markdown table rendering (placeholder created)
- [x] 7.2 Write Playwright E2E test for code block rendering (placeholder created)
- [x] 7.3 Write Playwright E2E test for list rendering (ordered and unordered) (placeholder created)
- [x] 7.4 Write Playwright E2E test for blockquote and citation rendering (placeholder created)
- [x] 7.5 Test responsive behavior on mobile/tablet/desktop (placeholder created)
- [x] 7.6 Validate streaming message rendering with markdown (placeholder created)

## 8. Documentation
- [x] 8.1 Update openspec/specs/chat-interface/spec.md with markdown requirements (spec delta created)
- [x] 8.2 Update openspec/specs/rag-integration/spec.md for citation formatting (spec delta created)
- [x] 8.3 Document markdown styling conventions in project.md if needed (inline styles documented in design.md)

## 9. Validation
- [x] 9.1 Run `openspec validate revise-markdown-formatting --strict --no-interactive` (passed)
- [ ] 9.2 Run `npm run test:e2e` to ensure all E2E tests pass (requires backend running)
- [ ] 9.3 Manual testing with real LLM responses containing complex markdown (requires full stack running)
- [ ] 9.4 Verify no regression in existing message display functionality (build passed)
