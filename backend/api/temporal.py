"""API endpoints for temporal analysis configuration."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.base import get_db
from backend.models.file import FileDB, TemporalConfigUpdate
from backend.utils.auth import get_current_user_id
from backend.tasks.document_tasks import process_document


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["temporal"])


@router.get("/{file_id}/temporal-metadata")
async def get_temporal_metadata(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get temporal metadata for a file.

    Returns temporal analysis results including detected date columns,
    time range, and lead time statistics.
    """
    # Get file and verify ownership
    file_db = db.query(FileDB).filter(
        FileDB.id == file_id,
        FileDB.user_id == user_id,
    ).first()

    if not file_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return {
        "file_id": str(file_db.id),
        "filename": file_db.filename,
        "temporal_metadata": file_db.temporal_metadata,
    }


@router.patch("/{file_id}/temporal-config")
async def update_temporal_config(
    file_id: UUID,
    config: TemporalConfigUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Update temporal configuration for a file.

    Allows user to manually specify date columns and lead time pairs
    if automatic detection is incorrect or incomplete.

    This will trigger re-processing of the document with the new configuration.
    """
    # Get file and verify ownership
    file_db = db.query(FileDB).filter(
        FileDB.id == file_id,
        FileDB.user_id == user_id,
    ).first()

    if not file_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Update temporal metadata with user configuration
    current_metadata = file_db.temporal_metadata or {}

    if config.date_columns is not None:
        current_metadata['user_configured_columns'] = config.date_columns

    if config.lead_time_pairs is not None:
        current_metadata['user_configured_lead_time_pairs'] = config.lead_time_pairs

    file_db.temporal_metadata = current_metadata
    db.commit()

    logger.info(f"Updated temporal config for file {file_id}: {config.model_dump()}")

    # Trigger re-processing with new configuration
    # Note: This will re-parse and re-index the document
    process_document.delay(str(file_id))

    return {
        "success": True,
        "message": "Temporal configuration updated. Document is being re-processed.",
        "file_id": str(file_db.id),
        "temporal_metadata": file_db.temporal_metadata,
    }
