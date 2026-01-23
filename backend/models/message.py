"""Message models for database and API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, CheckConstraint, JSON
from sqlalchemy.orm import relationship

from backend.db import Base, UUID as DBUUID


class MessageRole(str, Enum):
    """Enum for message roles."""

    USER = "user"
    ASSISTANT = "assistant"


# SQLAlchemy ORM Model
class MessageDB(Base):
    """Database model for messages."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="check_role"),
    )

    id = Column(DBUUID, primary_key=True, default=uuid4)
    conversation_id = Column(
        DBUUID,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    conversation = relationship("ConversationDB", back_populates="messages")


# Pydantic Models for API

class CitationMetadata(BaseModel):
    """Schema for citation metadata."""

    filename: str
    sheet_name: Optional[str] = None  # For Excel files
    cell_ref: Optional[str] = None  # For Excel files (e.g., "C12")
    page: Optional[int] = None  # For PDF/Word/PowerPoint
    row: Optional[int] = None  # For Excel files
    column: Optional[int] = None  # For Excel files
    value: Optional[str] = None  # The actual value from the source


class MessageBase(BaseModel):
    """Base schema for message."""

    role: MessageRole
    content: str = Field(..., min_length=1, max_length=50000)
    citations: Optional[List[CitationMetadata]] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    conversation_id: UUID


class Message(MessageBase):
    """Schema for message response."""

    id: UUID
    conversation_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MessageStreamChunk(BaseModel):
    """Schema for streaming message chunks."""

    content: str
    is_final: bool = False
    citations: Optional[List[CitationMetadata]] = None
