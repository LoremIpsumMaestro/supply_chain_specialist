# Implementation Tasks: Chat Interface with Conversation History

## 1. Backend Setup

### 1.1 Database Schema
- [x] Create migration script for `conversations` table with fields: id, user_id, title, created_at, updated_at, expires_at
- [x] Create migration script for `messages` table with fields: id, conversation_id, role, content, citations, created_at
- [x] Add indexes for query optimization (user_id, expires_at, conversation_id)
- [x] Add foreign key constraints with CASCADE delete
- [x] Test migrations (up and down)

### 1.2 Database Models
- [x] Create Pydantic models for Conversation (backend/models/conversation.py)
- [x] Create Pydantic models for Message (backend/models/message.py)
- [x] Create SQLAlchemy ORM models for database access
- [x] Add validation rules (role enum, content length, etc.)

### 1.3 API Endpoints - Conversations
- [x] Implement `GET /api/conversations` (list user's conversations)
- [x] Implement `POST /api/conversations` (create new conversation)
- [x] Implement `GET /api/conversations/:id` (get conversation with messages)
- [x] Implement `DELETE /api/conversations/:id` (delete conversation)
- [x] Add authentication middleware (JWT verification)
- [x] Add error handling and validation

### 1.4 API Endpoints - Messages
- [x] Implement `POST /api/conversations/:id/messages` (send message with SSE streaming)
- [x] Setup streaming response with Vercel AI SDK compatibility
- [x] Integrate with LLM service (OpenAI/Anthropic)
- [x] Add citation extraction logic for responses
- [x] Add rate limiting (10 messages/minute per user)
- [x] Add error handling for LLM failures

### 1.5 Data Purge Automation
- [x] Setup pg_cron extension in PostgreSQL
- [x] Create purge job to delete expired conversations (WHERE expires_at < NOW())
- [x] Create purge job to delete orphaned messages
- [x] Test purge job execution and verify data deletion
- [x] Add logging for purge operations

### 1.6 Backend Testing
- [ ] Write unit tests for conversation CRUD operations
- [ ] Write unit tests for message streaming
- [ ] Write integration tests for full conversation flow
- [ ] Write tests for 24-hour purge logic
- [ ] Write tests for error handling and validation

## 2. Frontend Core

### 2.1 Project Setup
- [x] Initialize Next.js 15 project structure (if not exists)
- [x] Install dependencies: @vercel/ai, zustand, react-hook-form, zod, react-dropzone, date-fns
- [x] Install shadcn/ui components: Button, Input, ScrollArea, Badge, Dialog, DropdownMenu
- [x] Setup TailwindCSS configuration with project colors
- [x] Create base layout component (frontend/app/layout.tsx)

### 2.2 State Management
- [x] Create Zustand store for conversations (frontend/store/conversationStore.ts)
- [x] Add actions: loadConversations, selectConversation, createConversation, deleteConversation
- [x] Create Zustand store for messages (frontend/store/messageStore.ts)
- [x] Add actions: loadMessages, addMessage, streamMessage
- [x] Create Zustand store for UI state (sidebar open/closed, loading states)

### 2.3 API Client
- [x] Create API client utility (frontend/lib/api.ts) with fetch wrapper
- [x] Implement conversation service (getConversations, createConversation, deleteConversation)
- [x] Implement message service (getMessages, sendMessage with streaming support)
- [x] Add authentication header injection (JWT token)
- [x] Add error handling and retry logic

### 2.4 Chat Components - Layout
- [x] Create main chat page (frontend/app/chat/page.tsx)
- [x] Create ChatLayout component with sidebar + chat area (frontend/components/chat/ChatLayout.tsx)
- [x] Create Sidebar component (frontend/components/chat/Sidebar.tsx)
- [x] Create ConversationList component (frontend/components/chat/ConversationList.tsx)
- [x] Create ConversationItem component (frontend/components/chat/ConversationItem.tsx)

### 2.5 Chat Components - Messages
- [x] Create MessageList component with virtualized scrolling (frontend/components/chat/MessageList.tsx)
- [x] Create Message component for user/assistant messages (frontend/components/chat/Message.tsx)
- [x] Create MessageInput component with send button (frontend/components/chat/MessageInput.tsx)
- [x] Create LoadingIndicator component for assistant thinking state (frontend/components/chat/LoadingIndicator.tsx)
- [x] Create Citation component for inline source display (frontend/components/chat/Citation.tsx)

### 2.6 Conversation Management UI
- [x] Add "New Conversation" button in sidebar
- [x] Implement conversation selection (highlight active conversation)
- [x] Add conversation delete button with confirmation dialog
- [x] Add conversation title display (truncate if too long)
- [x] Add timestamp display for each conversation (using date-fns)

## 3. Streaming & Citations

### 3.1 Streaming Integration
- [x] Integrate Vercel AI SDK useChat hook in MessageInput component
- [x] Connect streaming endpoint to backend POST /api/conversations/:id/messages
- [x] Display streaming response incrementally in MessageList
- [x] Handle streaming errors (timeout, connection lost)
- [x] Add retry mechanism for failed streams

### 3.2 Citation Display
- [x] Parse citation metadata from assistant responses (JSONB format)
- [x] Render Citation component inline with message content
- [x] Display Excel citations with format: "📄 filename | sheet | cell"
- [x] Display document citations with format: "📄 filename | page X"
- [x] Add tooltip on hover showing full citation details
- [x] Style citations with badge/chip component from shadcn/ui

### 3.3 Testing Streaming
- [ ] Test streaming with OpenAI model (gpt-3.5-turbo)
- [ ] Test streaming with Anthropic model (claude-3-sonnet)
- [ ] Test citation parsing for Excel sources
- [ ] Test citation parsing for PDF/Word/PowerPoint sources
- [ ] Test error handling (model timeout, invalid response)

## 4. File Upload

### 4.1 Upload UI
- [ ] Add upload button in MessageInput area (frontend/components/chat/FileUploadButton.tsx)
- [ ] Integrate react-dropzone for drag-and-drop functionality
- [ ] Add file type validation (.xlsx, .csv, .pdf, .docx, .pptx, .txt)
- [ ] Add file size validation (max 50MB)
- [ ] Display upload progress bar (frontend/components/chat/UploadProgress.tsx)

### 4.2 Upload Logic
- [ ] Implement file upload to POST /api/files endpoint
- [ ] Display success message with filename in chat
- [ ] Display error message if upload fails (with reason)
- [ ] Add file icon/badge to show uploaded files in conversation
- [ ] Support multiple file uploads in one conversation

### 4.3 Testing File Upload
- [ ] Test upload with each supported file type
- [ ] Test upload with oversized file (should fail gracefully)
- [ ] Test upload with invalid file type (should reject)
- [ ] Test multiple file uploads
- [ ] Test upload progress indication

## 5. Responsive Design

### 5.1 Desktop Layout (>1024px)
- [x] Persistent sidebar on the left (300px width)
- [x] Main chat area occupies remaining space
- [x] Fixed input area at bottom
- [ ] Test layout on 1920x1080 and 1366x768 resolutions

### 5.2 Tablet Layout (768px-1024px)
- [x] Add sidebar toggle button in header
- [x] Sidebar overlays chat area when open
- [x] Appropriate spacing and touch targets
- [ ] Test layout on iPad (1024x768) and iPad Pro (1366x1024)

### 5.3 Mobile Layout (<768px)
- [x] Hide sidebar behind hamburger menu
- [x] Full-width chat area
- [x] Adapt input area for soft keyboard (viewport units)
- [x] Ensure keyboard doesn't obscure input field
- [ ] Test layout on iPhone (375x667) and Android (360x640)

### 5.4 Responsive Testing
- [ ] Test all breakpoints in browser dev tools
- [ ] Test on real devices (iOS and Android)
- [ ] Verify touch interactions work on mobile/tablet
- [ ] Test landscape and portrait orientations

## 6. Auto-scroll & Polish

### 6.1 Auto-scroll Implementation
- [x] Implement auto-scroll to bottom on new user message
- [x] Implement auto-scroll during assistant streaming
- [x] Detect when user manually scrolls up (disable auto-scroll)
- [x] Add "New message" pill at bottom when auto-scroll disabled
- [x] Click pill to re-enable auto-scroll and jump to bottom
- [x] Smooth scroll animation (not instant jump)

### 6.2 UX Polish
- [x] Add loading skeleton for conversation list
- [x] Add empty state when no conversations exist
- [x] Add empty state when conversation has no messages
- [x] Add typing indicator animation during assistant response
- [x] Add message timestamp display (relative time: "2 minutes ago")
- [x] Add hover states for interactive elements

### 6.3 Accessibility
- [ ] Add ARIA labels to all interactive elements
- [ ] Ensure keyboard navigation works (Tab, Enter, Escape)
- [ ] Add focus indicators for keyboard users
- [ ] Test with screen reader (VoiceOver or NVDA)
- [ ] Ensure color contrast meets WCAG 2.1 AA standards

## 7. Testing & Validation

### 7.1 Unit Tests
- [ ] Write tests for Zustand stores (conversation, message, UI state)
- [ ] Write tests for API client functions
- [ ] Write tests for React components (Message, MessageList, Citation, etc.)
- [ ] Achieve 80% code coverage (per project.md)

### 7.2 Integration Tests
- [ ] Test full chat flow: create conversation → send message → receive response
- [ ] Test conversation management: create → select → delete
- [ ] Test file upload: select file → upload → receive confirmation
- [ ] Test streaming: send message → stream response → display citations
- [ ] Test 24-hour purge: create conversation → wait 24h → verify deletion (or mock time)

### 7.3 E2E Tests with Playwright
- [ ] Setup Playwright test environment
- [ ] Write test: User creates new conversation and sends first message
- [ ] Write test: User uploads file and asks question about it
- [ ] Write test: User switches between multiple conversations
- [ ] Write test: User deletes conversation
- [ ] Write test: Responsive layout works on mobile/tablet/desktop
- [ ] Run all E2E tests and verify they pass

### 7.4 Manual Testing
- [ ] Test with real documents (Excel, PDF, Word, PowerPoint)
- [ ] Test citation accuracy with complex Excel files
- [ ] Test performance with long conversations (100+ messages)
- [ ] Test on slow network (throttle to 3G)
- [ ] Test browser compatibility (Chrome, Firefox, Safari, Edge)

## 8. Documentation & Deployment

### 8.1 Documentation
- [x] Write README for backend API endpoints
- [x] Write README for frontend components and architecture
- [x] Document environment variables required (.env.example)
- [x] Document database schema and migrations
- [x] Add inline code comments for complex logic

### 8.2 Deployment Preparation
- [x] Setup Docker Compose for local development (backend + database + Redis)
- [x] Create Dockerfile for backend (FastAPI)
- [x] Configure Next.js for production build
- [x] Setup environment variables for production
- [x] Verify all secrets are not hardcoded

### 8.3 Deployment
- [ ] Deploy backend to Fly.io or Railway
- [ ] Deploy frontend to Vercel
- [ ] Setup PostgreSQL database (managed or Docker)
- [ ] Setup Redis instance (managed or Docker)
- [ ] Configure CORS for frontend-backend communication
- [ ] Verify 24-hour purge job is running

### 8.4 Post-Deployment Validation
- [ ] Smoke test: Create conversation and send message
- [ ] Verify streaming works in production
- [ ] Upload test file and verify indexing
- [ ] Check database for proper data storage
- [ ] Monitor logs for errors
- [ ] Verify purge job runs after 24 hours
