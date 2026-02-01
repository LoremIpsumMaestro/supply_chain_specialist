"""File model for uploaded documents."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from backend.db import Base, UUID as DBUUID, JSON


class FileType(str, Enum):
    """Supported file types."""
    EXCEL = "excel"
    CSV = "csv"
    PDF = "pdf"
    WORD = "word"
    POWERPOINT = "powerpoint"
    TEXT = "text"


class ProcessingStatus(str, Enum):
    """File processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# SQLAlchemy ORM Model
class FileDB(Base):
    """File database model."""
    __tablename__ = "files"

    id = Column(DBUUID, primary_key=True, default=uuid4)
    user_id = Column(DBUUID, nullable=False)
    conversation_id = Column(DBUUID, ForeignKey("conversations.id", ondelete="CASCADE"))
    filename = Column(String(255), nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    minio_object_key = Column(String(500), nullable=False)
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    error_message = Column(Text)
    temporal_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    conversation = relationship("ConversationDB", back_populates="files")

    def __repr__(self):
        return f"<File {self.filename} ({self.file_type.value})>"


# Pydantic Models for API
class FileBase(BaseModel):
    """Base file schema."""
    filename: str = Field(..., max_length=255)
    file_type: FileType
    file_size_bytes: int = Field(..., gt=0, le=52428800)  # Max 50MB
    conversation_id: Optional[UUID] = None

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename has allowed extension."""
        allowed_extensions = {
            '.xlsx', '.xls', '.csv', '.pdf',
            '.docx', '.doc', '.pptx', '.ppt', '.txt'
        }
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'Filename must have one of these extensions: {allowed_extensions}')
        return v


class FileCreate(FileBase):
    """Schema for creating a file record."""
    user_id: UUID
    minio_object_key: str
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))


class FileResponse(FileBase):
    """Schema for file response."""
    id: UUID
    user_id: UUID
    minio_object_key: str
    processing_status: ProcessingStatus
    error_message: Optional[str] = None
    temporal_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class FileUpdate(BaseModel):
    """Schema for updating file status."""
    processing_status: Optional[ProcessingStatus] = None
    error_message: Optional[str] = None


# Temporal Metadata Schemas
class TimeRange(BaseModel):
    """Time range schema."""
    earliest: str  # ISO date format YYYY-MM-DD
    latest: str


class LeadTimeStats(BaseModel):
    """Lead time statistics schema."""
    mean_days: float
    median_days: float
    max_days: float
    min_days: float
    std_days: float
    outliers: List[float]
    total_records: int


class TemporalMetadata(BaseModel):
    """Temporal metadata schema for files."""
    upload_date: datetime
    detected_date_columns: List[str]
    user_configured_columns: Optional[List[str]] = None
    time_range: Optional[TimeRange] = None
    lead_time_stats: Optional[LeadTimeStats] = None


class TemporalConfigUpdate(BaseModel):
    """Schema for updating temporal configuration."""
    date_columns: Optional[List[str]] = None
    lead_time_pairs: Optional[List[List[str]]] = None  # List of [start_col, end_col] pairs


# MIME type mappings
MIME_TYPE_MAP = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileType.EXCEL,
    'application/vnd.ms-excel': FileType.EXCEL,
    'text/csv': FileType.CSV,
    'application/pdf': FileType.PDF,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.WORD,
    'application/msword': FileType.WORD,
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': FileType.POWERPOINT,
    'application/vnd.ms-powerpoint': FileType.POWERPOINT,
    'text/plain': FileType.TEXT,
}


def get_file_type_from_mime(mime_type: str) -> Optional[FileType]:
    """Get FileType from MIME type."""
    return MIME_TYPE_MAP.get(mime_type)
