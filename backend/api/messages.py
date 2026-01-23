"""API endpoints for messages with streaming support."""

import json
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import (
    ConversationDB,
    Message,
    MessageCreate,
    MessageDB,
    MessageRole,
)
from backend.services.llm_service import LLMService
from backend.utils.auth import get_current_user_id
from backend.utils.rate_limit import rate_limit

router = APIRouter(prefix="/api/conversations", tags=["messages"])


class SendMessageRequest(BaseModel):
    """Request schema for sending a message."""

    content: str


@router.post(
    "/{conversation_id}/messages",
    response_class=StreamingResponse,
)
@rate_limit(max_requests=10, window_seconds=60)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Send a message and stream the AI response.

    This endpoint:
    1. Validates the conversation belongs to the user
    2. Saves the user's message
    3. Streams the AI assistant's response
    4. Saves the complete assistant response

    Returns Server-Sent Events (SSE) stream compatible with Vercel AI SDK.
    """
    # Verify conversation exists and belongs to user
    conversation = (
        db.query(ConversationDB)
        .filter(
            ConversationDB.id == conversation_id,
            ConversationDB.user_id == user_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Save user message
    user_message = MessageDB(
        conversation_id=conversation_id,
        role=MessageRole.USER.value,
        content=request.content,
    )
    db.add(user_message)
    db.commit()

    # Get conversation history for context
    history = (
        db.query(MessageDB)
        .filter(MessageDB.conversation_id == conversation_id)
        .order_by(MessageDB.created_at.asc())
        .all()
    )

    # Initialize LLM service
    llm_service = LLMService()

    # Generate streaming response
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream for the response."""
        accumulated_content = ""
        citations = []

        try:
            async for chunk in llm_service.stream_response(
                conversation_history=history,
                conversation_id=conversation_id,
                db=db,
                user_id=user_id,
            ):
                accumulated_content += chunk.content

                if chunk.citations:
                    citations = chunk.citations

                # Format as SSE
                event_data = {
                    "content": chunk.content,
                    "is_final": chunk.is_final,
                }

                if chunk.citations:
                    event_data["citations"] = [c.dict() for c in chunk.citations]

                yield f"data: {json.dumps(event_data)}\n\n"

                # If final chunk, save the complete message
                if chunk.is_final:
                    assistant_message = MessageDB(
                        conversation_id=conversation_id,
                        role=MessageRole.ASSISTANT.value,
                        content=accumulated_content,
                        citations=[c.dict() for c in citations] if citations else None,
                    )
                    db.add(assistant_message)
                    db.commit()

        except Exception as e:
            # Send error event
            error_data = {
                "error": str(e),
                "is_final": True,
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{conversation_id}/messages", response_model=list[Message])
async def get_messages(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[Message]:
    """
    Get all messages for a conversation.

    Returns messages ordered by creation time (oldest first).
    Returns 404 if conversation doesn't exist or doesn't belong to the user.
    """
    # Verify conversation exists and belongs to user
    conversation = (
        db.query(ConversationDB)
        .filter(
            ConversationDB.id == conversation_id,
            ConversationDB.user_id == user_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Get messages
    messages = (
        db.query(MessageDB)
        .filter(MessageDB.conversation_id == conversation_id)
        .order_by(MessageDB.created_at.asc())
        .all()
    )

    return messages
