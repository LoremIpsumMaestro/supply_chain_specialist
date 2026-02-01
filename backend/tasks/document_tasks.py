"""Celery tasks for asynchronous document processing."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.tasks import celery_app
from backend.db.base import SessionLocal
from backend.models.file import FileDB, ProcessingStatus, FileType
from backend.services.storage_service import storage_service
from backend.services.document_parser import DocumentParserFactory


logger = logging.getLogger(__name__)


def _extract_temporal_metadata(chunks) -> dict:
    """
    Extract temporal metadata from parsed chunks.

    Args:
        chunks: List of DocumentChunk objects

    Returns:
        Dictionary with temporal metadata
    """
    from backend.services.temporal_service import temporal_service

    try:
        # Collect all detected temporal columns from chunks
        detected_columns = set()
        all_dates = []

        for chunk in chunks:
            if 'temporal_context' in chunk.metadata:
                tc = chunk.metadata['temporal_context']
                for key, value in tc.items():
                    if value:
                        detected_columns.add(key)
                        # Try to parse date for time range
                        try:
                            import pandas as pd
                            dt = pd.to_datetime(value)
                            all_dates.append(dt)
                        except Exception:
                            pass

        # Build temporal metadata
        metadata = {
            'upload_date': datetime.utcnow().isoformat(),
            'detected_date_columns': list(detected_columns),
            'user_configured_columns': None,
        }

        # Calculate time range if dates found
        if all_dates:
            earliest = min(all_dates)
            latest = max(all_dates)
            metadata['time_range'] = {
                'earliest': earliest.strftime('%Y-%m-%d'),
                'latest': latest.strftime('%Y-%m-%d'),
            }

        # Note: lead_time_stats would require re-parsing with DataFrame
        # For now, we skip it here (can be added in future optimization)
        metadata['lead_time_stats'] = None

        return metadata

    except Exception as e:
        logger.error(f"Error extracting temporal metadata: {e}", exc_info=True)
        return None


@celery_app.task(name="process_document", bind=True, max_retries=3)
def process_document(self, file_id: str):
    """
    Process uploaded document: parse, extract chunks, detect alerts, index in TypeSense.

    Args:
        file_id: UUID of the file to process

    Returns:
        dict with processing results
    """
    db: Session = SessionLocal()

    try:
        # Get file from database
        file_db = db.query(FileDB).filter(FileDB.id == UUID(file_id)).first()

        if not file_db:
            logger.error(f"File not found: {file_id}")
            return {"success": False, "error": "File not found"}

        # Update status to processing
        file_db.processing_status = ProcessingStatus.PROCESSING
        db.commit()

        logger.info(f"Processing file: {file_id} - {file_db.filename}")

        # Download file from MinIO
        file_bytes = storage_service.download_file(file_db.minio_object_key)

        if not file_bytes:
            raise Exception("Failed to download file from MinIO")

        # Parse document based on type
        parser = DocumentParserFactory.get_parser(file_db.file_type)
        chunks = parser.parse(file_bytes, file_db.filename)

        logger.info(f"Parsed {len(chunks)} chunks from {file_db.filename}")

        # Detect alerts in parallel with indexing
        from backend.services.alert_service import alert_detector
        from backend.models.alert import AlertDB

        alerts = alert_detector.detect_all_alerts(chunks)
        logger.info(f"Detected {len(alerts)} alerts in {file_db.filename}")

        # Save alerts to database
        for alert in alerts:
            alert_db = AlertDB(
                user_id=file_db.user_id,
                file_id=file_db.id,
                conversation_id=file_db.conversation_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                message=alert.message,
                metadata=alert.chunk_metadata,
                value=str(alert.value) if alert.value is not None else None,
            )
            db.add(alert_db)

        db.commit()
        logger.info(f"Saved {len(alerts)} alerts to database")

        # Index chunks in TypeSense with embeddings
        from backend.services.rag_service import rag_service

        success = rag_service.index_chunks(chunks, str(file_db.user_id), file_id)

        if not success:
            raise Exception("Failed to index chunks in TypeSense")

        logger.info(f"Successfully indexed {len(chunks)} chunks for file {file_id}")

        # Extract and store temporal metadata for Excel/CSV files
        temporal_metadata = None
        if file_db.file_type in [FileType.EXCEL, FileType.CSV]:
            temporal_metadata = _extract_temporal_metadata(chunks)
            if temporal_metadata:
                file_db.temporal_metadata = temporal_metadata
                logger.info(f"Stored temporal metadata: {temporal_metadata.get('detected_date_columns', [])}")

        # Update status to completed
        file_db.processing_status = ProcessingStatus.COMPLETED
        file_db.error_message = None
        db.commit()

        logger.info(f"Successfully processed file: {file_id}")

        return {
            "success": True,
            "file_id": file_id,
            "chunks_count": len(chunks),
        }

    except Exception as e:
        logger.error(f"Error processing file {file_id}: {e}", exc_info=True)

        # Update file status to failed
        try:
            file_db = db.query(FileDB).filter(FileDB.id == UUID(file_id)).first()
            if file_db:
                file_db.processing_status = ProcessingStatus.FAILED
                file_db.error_message = str(e)[:500]  # Truncate long errors
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update file status: {db_error}")

        # Retry on transient errors (network, timeout)
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(exc=e, countdown=5 ** self.request.retries)

        return {
            "success": False,
            "file_id": file_id,
            "error": str(e),
        }

    finally:
        db.close()
