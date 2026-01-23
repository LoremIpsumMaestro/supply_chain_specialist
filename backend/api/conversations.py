"""API endpoints for conversations."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import (
    Conversation,
    ConversationCreate,
    ConversationDB,
    ConversationUpdate,
    ConversationWithMessages,
    MessageDB,
)
from backend.utils.auth import get_current_user_id

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=List[Conversation])
async def list_conversations(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> List[Conversation]:
    """
    List all conversations for the current user.

    Returns conversations ordered by most recent activity (updated_at DESC).
    """
    conversations = (
        db.query(ConversationDB)
        .filter(ConversationDB.user_id == user_id)
        .order_by(ConversationDB.updated_at.desc())
        .all()
    )

    return conversations


@router.post("", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Conversation:
    """
    Create a new conversation.

    The conversation will automatically expire after 24 hours.
    """
    # Auto-generate title from first message if not provided
    title = conversation_data.title or "New Conversation"

    conversation = ConversationDB(
        user_id=user_id,
        title=title,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ConversationWithMessages:
    """
    Get a specific conversation with all its messages.

    Returns 404 if conversation doesn't exist or doesn't belong to the user.
    """
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

    # Load messages ordered by creation time
    messages = (
        db.query(MessageDB)
        .filter(MessageDB.conversation_id == conversation_id)
        .order_by(MessageDB.created_at.asc())
        .all()
    )

    # Convert to response model
    conversation_dict = {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "expires_at": conversation.expires_at,
        "messages": messages,
    }

    return ConversationWithMessages(**conversation_dict)


@router.patch("/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Conversation:
    """
    Update a conversation (currently only title can be updated).

    Returns 404 if conversation doesn't exist or doesn't belong to the user.
    """
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

    # Update fields
    if conversation_data.title is not None:
        conversation.title = conversation_data.title

    db.commit()
    db.refresh(conversation)

    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a conversation and all its messages.

    Returns 404 if conversation doesn't exist or doesn't belong to the user.
    Messages are automatically deleted via CASCADE constraint.
    """
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

    db.delete(conversation)
    db.commit()
