"""Conversation models for database and API."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from backend.db import Base, UUID as DBUUID


# SQLAlchemy ORM Model
class ConversationDB(Base):
    """Database model for conversations."""

    __tablename__ = "conversations"

    id = Column(DBUUID, primary_key=True, default=uuid4)
    user_id = Column(DBUUID, nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(hours=24),
        index=True,
    )

    # Relationships
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")
    files = relationship("FileDB", back_populates="conversation", cascade="all, delete-orphan")


# Pydantic Models for API

class ConversationBase(BaseModel):
    """Base schema for conversation."""

    title: Optional[str] = Field(None, max_length=255)


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    pass


class ConversationUpdate(ConversationBase):
    """Schema for updating a conversation."""

    pass


class Conversation(ConversationBase):
    """Schema for conversation response."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(Conversation):
    """Schema for conversation with messages."""

    messages: List["Message"] = []

    class Config:
        from_attributes = True


# Import Message model for type hints
from backend.models.message import Message  # noqa: E402

ConversationWithMessages.model_rebuild()
