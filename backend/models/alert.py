"""Alert model for Supply Chain anomalies."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship

from backend.db import Base, UUID as DBUUID


class AlertType(str, Enum):
    """Types of supply chain alerts."""
    NEGATIVE_STOCK = "negative_stock"
    DATE_INCONSISTENCY = "date_inconsistency"
    NEGATIVE_QUANTITY = "negative_quantity"
    LEAD_TIME_OUTLIER = "lead_time_outlier"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# SQLAlchemy ORM Model
class AlertDB(Base):
    """Alert database model."""
    __tablename__ = "alerts"

    id = Column(DBUUID, primary_key=True, default=uuid4)
    user_id = Column(DBUUID, nullable=False, index=True)
    file_id = Column(DBUUID, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(DBUUID, ForeignKey("conversations.id", ondelete="CASCADE"))
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, index=True)
    message = Column(Text, nullable=False)
    source_metadata = Column(JSON)  # Source metadata (cell_ref, page, etc.)
    value = Column(Text)  # The problematic value
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Alert {self.alert_type.value} ({self.severity.value})>"


# Pydantic Models for API
class AlertBase(BaseModel):
    """Base alert schema."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    metadata: Optional[Dict[str, Any]] = None
    value: Optional[str] = None


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    user_id: UUID
    file_id: UUID
    conversation_id: Optional[UUID] = None


class AlertResponse(AlertBase):
    """Schema for alert response."""
    id: UUID
    user_id: UUID
    file_id: UUID
    conversation_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
