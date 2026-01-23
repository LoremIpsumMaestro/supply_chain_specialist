"""File upload and management API endpoints."""

import io
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.db.base import get_db
from backend.models.file import (
    FileCreate,
    FileDB,
    FileResponse,
    FileType,
    ProcessingStatus,
    get_file_type_from_mime,
)
from backend.services.storage_service import storage_service
from backend.utils.auth import get_current_user_id
from backend.config import settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/files", tags=["files"])


# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
    'text/csv',  # .csv
    'application/pdf',  # .pdf
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/msword',  # .doc
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
    'application/vnd.ms-powerpoint',  # .ppt
    'text/plain',  # .txt
}


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Upload a Supply Chain document.

    Supported formats: Excel (.xlsx, .xls), CSV, PDF, Word (.docx), PowerPoint (.pptx), Text (.txt)
    Max size: 50MB
    Files are automatically deleted after 24 hours.
    """
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({settings.MAX_FILE_SIZE_BYTES} bytes / 50MB)"
        )

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed types: {ALLOWED_MIME_TYPES}"
        )

    # Validate extension matches MIME type
    file_type = get_file_type_from_mime(file.content_type)
    if not file_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Could not determine file type from MIME type: {file.content_type}"
        )

    # Validate filename extension
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file extension. Allowed extensions: {settings.ALLOWED_EXTENSIONS}"
        )

    try:
        # Generate unique file ID and object key
        file_id = uuid4()
        object_key = storage_service.generate_object_key(user_id, file_id, file.filename)

        # Upload to MinIO
        success = storage_service.upload_file(
            file=file.file,
            object_key=object_key,
            content_type=file.content_type,
            file_size=file_size,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
            )

        # Create database record
        conv_id = UUID(conversation_id) if conversation_id else None
        file_create = FileCreate(
            user_id=user_id,
            conversation_id=conv_id,
            filename=file.filename,
            file_type=file_type,
            file_size_bytes=file_size,
            minio_object_key=object_key,
        )

        file_db = FileDB(
            id=file_id,
            user_id=file_create.user_id,
            conversation_id=file_create.conversation_id,
            filename=file_create.filename,
            file_type=file_create.file_type,
            file_size_bytes=file_create.file_size_bytes,
            minio_object_key=file_create.minio_object_key,
            processing_status=ProcessingStatus.PENDING,
            expires_at=file_create.expires_at,
        )

        db.add(file_db)
        db.commit()
        db.refresh(file_db)

        logger.info(f"File uploaded successfully: {file_id} - {file.filename}")

        # Trigger Celery task for document processing
        from backend.tasks.document_tasks import process_document
        process_document.delay(str(file_id))
        logger.info(f"Queued document processing task for file: {file_id}")

        return FileResponse.model_validate(file_db)

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        # Cleanup: try to delete from MinIO if DB insert fails
        if 'object_key' in locals():
            storage_service.delete_file(object_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("", response_model=List[FileResponse])
def list_files(
    conversation_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    List uploaded files for the current user.

    Optionally filter by conversation_id.
    Files are ordered by created_at DESC (most recent first).
    """
    query = db.query(FileDB).filter(FileDB.user_id == user_id)

    if conversation_id:
        query = query.filter(FileDB.conversation_id == conversation_id)

    files = query.order_by(FileDB.created_at.desc()).all()
    return [FileResponse.model_validate(f) for f in files]


@router.get("/{file_id}", response_model=FileResponse)
def get_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get file metadata by ID."""
    file_db = db.query(FileDB).filter(
        FileDB.id == file_id,
        FileDB.user_id == user_id
    ).first()

    if not file_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse.model_validate(file_db)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Delete a file.

    Removes file from both MinIO storage and database.
    """
    file_db = db.query(FileDB).filter(
        FileDB.id == file_id,
        FileDB.user_id == user_id
    ).first()

    if not file_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    try:
        # Delete from MinIO
        storage_service.delete_file(file_db.minio_object_key)

        # Delete from database
        db.delete(file_db)
        db.commit()

        logger.info(f"File deleted successfully: {file_id}")
        return None

    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file: {str(e)}"
        )
