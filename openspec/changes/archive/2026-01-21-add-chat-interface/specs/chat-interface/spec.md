# Chat Interface Specification

## ADDED Requirements

### Requirement: Conversation Display
The system SHALL provide a chat interface that displays messages in chronological order with clear distinction between user and assistant messages.

#### Scenario: User sends message
- **WHEN** a user types a message and presses send
- **THEN** the message appears immediately in the chat with user styling
- **AND** a loading indicator appears for the assistant response

#### Scenario: Assistant response streaming
- **WHEN** the assistant begins responding
- **THEN** the response appears incrementally as it streams
- **AND** the interface auto-scrolls to show new content

#### Scenario: Multiple messages display
- **WHEN** a conversation contains multiple messages
- **THEN** all messages display in chronological order (oldest first)
- **AND** each message shows the sender (user/assistant)
- **AND** each message shows a timestamp

### Requirement: Conversation History Persistence
The system SHALL persist conversations to the database and allow users to retrieve and resume previous conversations.

#### Scenario: Conversation saved automatically
- **WHEN** a user sends a message in a new conversation
- **THEN** a conversation record is created in the database
- **AND** all subsequent messages are linked to that conversation
- **AND** the conversation is assigned a unique ID

#### Scenario: User retrieves conversation list
- **WHEN** a user opens the application
- **THEN** a list of their previous conversations is displayed
- **AND** each conversation shows a title or first message preview
- **AND** conversations are ordered by most recent activity

#### Scenario: User selects previous conversation
- **WHEN** a user clicks on a previous conversation
- **THEN** all messages from that conversation are loaded and displayed
- **AND** the user can continue the conversation with new messages

#### Scenario: Conversation purge after 24 hours
- **WHEN** 24 hours have elapsed since conversation creation
- **THEN** the conversation and all associated messages are permanently deleted
- **AND** the user can no longer access that conversation

### Requirement: File Upload in Chat
The system SHALL allow users to upload documents directly within the chat interface for analysis.

#### Scenario: User uploads document
- **WHEN** a user clicks the upload button or drags a file into the chat
- **THEN** a file picker opens showing supported formats (Excel, PDF, Word, PowerPoint, CSV, Text)
- **AND** the selected file is validated for type and size
- **AND** the file upload progress is displayed

#### Scenario: Upload success
- **WHEN** a file upload completes successfully
- **THEN** a confirmation message appears in the chat
- **AND** the file name is displayed with a visual indicator
- **AND** the file is available for RAG indexing
- **AND** the user can immediately ask questions about the file

#### Scenario: Upload failure
- **WHEN** a file upload fails (invalid type, size limit, or network error)
- **THEN** an error message appears explaining the issue
- **AND** the upload is not added to the conversation
- **AND** the user can retry the upload

#### Scenario: Multiple file upload
- **WHEN** a user uploads multiple files in one conversation
- **THEN** each file is processed and indexed separately
- **AND** all files are available for cross-document analysis
- **AND** citations indicate which file contains the referenced information

### Requirement: Citation Display
The system SHALL display citations inline with assistant responses to show the source of information.

#### Scenario: Response with Excel citation
- **WHEN** the assistant provides information from an Excel file
- **THEN** the citation includes the filename, sheet name, and cell reference
- **AND** the citation is formatted as: "Selon la cellule C12 (feuille 'Stocks' du fichier production.xlsx): [value]"
- **AND** the citation is visually distinguished (e.g., with highlighting or icon)

#### Scenario: Response with document citation
- **WHEN** the assistant provides information from a PDF, Word, or PowerPoint file
- **THEN** the citation includes the filename and page/slide number if available
- **AND** the citation is formatted appropriately for the document type

#### Scenario: Response without source
- **WHEN** the assistant cannot find relevant information in uploaded documents
- **THEN** the assistant clearly states that no relevant information was found
- **AND** does not provide unsourced information that could be hallucinated

### Requirement: Conversation Management
The system SHALL allow users to create new conversations, delete conversations, and switch between conversations.

#### Scenario: User creates new conversation
- **WHEN** a user clicks the "New Conversation" button
- **THEN** a new empty conversation is created
- **AND** the chat interface is cleared
- **AND** the new conversation becomes the active conversation

#### Scenario: User deletes conversation
- **WHEN** a user clicks delete on a conversation in the sidebar
- **THEN** a confirmation dialog appears
- **AND** if confirmed, the conversation and all messages are deleted immediately
- **AND** if this was the active conversation, a new empty conversation is created

#### Scenario: User switches conversations
- **WHEN** a user clicks on a different conversation in the sidebar
- **THEN** the current conversation view is replaced with the selected conversation
- **AND** all messages from the selected conversation are loaded and displayed
- **AND** the selected conversation becomes the active conversation

### Requirement: Responsive Design
The system SHALL provide a responsive interface that works on desktop, tablet, and mobile devices.

#### Scenario: Desktop layout
- **WHEN** the interface is displayed on a desktop screen (>1024px)
- **THEN** the sidebar with conversation list is visible on the left
- **AND** the chat area occupies the main content area
- **AND** the input area is fixed at the bottom

#### Scenario: Mobile layout
- **WHEN** the interface is displayed on a mobile screen (<768px)
- **THEN** the conversation list is hidden behind a hamburger menu
- **AND** the chat area occupies the full width
- **AND** the input area adapts to smaller screen size
- **AND** the keyboard does not obscure the input area when open

#### Scenario: Tablet layout
- **WHEN** the interface is displayed on a tablet screen (768px-1024px)
- **THEN** the interface adapts with appropriate spacing and sizing
- **AND** touch targets are appropriately sized for touch interaction

### Requirement: Message Input
The system SHALL provide an input area for users to type and send messages.

#### Scenario: User types message
- **WHEN** a user types in the input field
- **THEN** the text is displayed with appropriate formatting
- **AND** the send button is enabled when text is present
- **AND** the send button is disabled when the field is empty

#### Scenario: User sends message with Enter key
- **WHEN** a user presses Enter in the input field
- **THEN** the message is sent (same as clicking send button)
- **AND** the input field is cleared

#### Scenario: User adds new line with Shift+Enter
- **WHEN** a user presses Shift+Enter in the input field
- **THEN** a new line is added to the message
- **AND** the message is not sent

#### Scenario: Input disabled during processing
- **WHEN** the assistant is processing a response
- **THEN** the input field is disabled
- **AND** a visual indicator shows the system is processing
- **AND** the user cannot send additional messages until processing completes

### Requirement: Auto-scroll Behavior
The system SHALL automatically scroll to show new messages as they appear.

#### Scenario: New message auto-scroll
- **WHEN** a new message appears (user or assistant)
- **THEN** the chat view automatically scrolls to show the new message
- **AND** the scroll is smooth (not instant jump)

#### Scenario: User has scrolled up
- **WHEN** the user has manually scrolled up to view previous messages
- **AND** a new message arrives
- **THEN** the auto-scroll is suppressed
- **AND** a "new message" indicator appears
- **AND** clicking the indicator scrolls to the latest message

#### Scenario: Streaming response auto-scroll
- **WHEN** an assistant response is streaming
- **THEN** the view automatically scrolls to keep the streaming text visible
- **AND** the scroll keeps pace with the streaming content
