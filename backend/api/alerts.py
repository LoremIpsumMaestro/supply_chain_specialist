"""Alert API endpoints for Supply Chain anomaly alerts."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.db.base import get_db
from backend.models.alert import AlertDB, AlertResponse, AlertSeverity
from backend.utils.auth import get_current_user_id


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/files/{file_id}", response_model=List[AlertResponse])
def get_file_alerts(
    file_id: UUID,
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Get all alerts for a specific file.

    Optionally filter by severity level.
    """
    query = db.query(AlertDB).filter(
        AlertDB.file_id == file_id,
        AlertDB.user_id == user_id,
    )

    if severity:
        query = query.filter(AlertDB.severity == severity)

    alerts = query.order_by(AlertDB.severity.desc(), AlertDB.created_at.desc()).all()

    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.get("/conversations/{conversation_id}", response_model=List[AlertResponse])
def get_conversation_alerts(
    conversation_id: UUID,
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Get all alerts for a specific conversation.

    Returns alerts from all files in the conversation.
    Optionally filter by severity level.
    """
    query = db.query(AlertDB).filter(
        AlertDB.conversation_id == conversation_id,
        AlertDB.user_id == user_id,
    )

    if severity:
        query = query.filter(AlertDB.severity == severity)

    alerts = query.order_by(AlertDB.severity.desc(), AlertDB.created_at.desc()).all()

    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.get("", response_model=List[AlertResponse])
def list_user_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=500, description="Max number of alerts to return"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Get all alerts for the current user.

    Optionally filter by severity level.
    Returns most recent alerts first.
    """
    query = db.query(AlertDB).filter(AlertDB.user_id == user_id)

    if severity:
        query = query.filter(AlertDB.severity == severity)

    alerts = query.order_by(AlertDB.severity.desc(), AlertDB.created_at.desc()).limit(limit).all()

    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.get("/stats", response_model=dict)
def get_alert_stats(
    conversation_id: Optional[UUID] = Query(None, description="Filter by conversation"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Get alert statistics for the user.

    Returns count of alerts by type and severity.
    """
    query = db.query(AlertDB).filter(AlertDB.user_id == user_id)

    if conversation_id:
        query = query.filter(AlertDB.conversation_id == conversation_id)

    alerts = query.all()

    # Count by severity
    severity_counts = {
        'critical': 0,
        'warning': 0,
        'info': 0,
    }

    # Count by type
    type_counts = {
        'negative_stock': 0,
        'date_inconsistency': 0,
        'negative_quantity': 0,
        'lead_time_outlier': 0,
    }

    for alert in alerts:
        severity_counts[alert.severity.value] += 1
        type_counts[alert.alert_type.value] += 1

    return {
        'total': len(alerts),
        'by_severity': severity_counts,
        'by_type': type_counts,
    }
