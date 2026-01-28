"""MinIO storage service for file uploads with 24h TTL."""

import io
import logging
from typing import BinaryIO, Optional
from uuid import UUID

from minio import Minio
from minio.error import S3Error
from minio.commonconfig import ENABLED
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Filter

from backend.config import settings


logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage in MinIO with automatic TTL."""

    def __init__(self):
        """Initialize MinIO client and ensure bucket exists with TTL policy."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,  # Use HTTP for local development, HTTPS in production
        )
        self.bucket_name = settings.MINIO_BUCKET
        try:
            self._ensure_bucket_exists()
            self._configure_lifecycle_policy()
        except Exception as e:
            logger.warning(f"MinIO not available, file storage will be limited: {e}")
            logger.warning("To enable file storage, please start MinIO service")

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
            else:
                logger.info(f"MinIO bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise

    def _configure_lifecycle_policy(self) -> None:
        """Configure lifecycle policy for 24h TTL."""
        try:
            # Rule to expire objects after 1 day (24 hours)
            # Filter with empty prefix applies to all objects
            rule = Rule(
                rule_id="expire-after-24h",
                status=ENABLED,
                rule_filter=Filter(prefix=""),
                expiration=Expiration(days=1),
            )
            config = LifecycleConfig([rule])
            self.client.set_bucket_lifecycle(self.bucket_name, config)
            logger.info(f"Configured 24h TTL lifecycle policy for bucket: {self.bucket_name}")
        except S3Error as e:
            logger.warning(f"Could not set lifecycle policy (may already exist): {e}")

    def generate_object_key(self, user_id: UUID, file_id: UUID, filename: str) -> str:
        """Generate unique object key with user isolation."""
        # Format: user_id/file_id/filename
        return f"{user_id}/{file_id}/{filename}"

    def upload_file(
        self,
        file: BinaryIO,
        object_key: str,
        content_type: str,
        file_size: int,
    ) -> bool:
        """
        Upload file to MinIO.

        Args:
            file: File-like object to upload
            object_key: Unique object key (user_id/file_id/filename)
            content_type: MIME type of the file
            file_size: Size of the file in bytes

        Returns:
            True if upload successful, False otherwise
        """
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=file,
                length=file_size,
                content_type=content_type,
            )
            logger.info(f"Uploaded file to MinIO: {object_key}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            return False

    def download_file(self, object_key: str) -> Optional[bytes]:
        """
        Download file from MinIO.

        Args:
            object_key: Object key to download

        Returns:
            File content as bytes, or None if error
        """
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Downloaded file from MinIO: {object_key}")
            return data
        except S3Error as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            return None

    def download_file_stream(self, object_key: str) -> Optional[io.BytesIO]:
        """
        Download file as stream for large files.

        Args:
            object_key: Object key to download

        Returns:
            BytesIO stream, or None if error
        """
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            stream = io.BytesIO(response.read())
            response.close()
            response.release_conn()
            stream.seek(0)
            return stream
        except S3Error as e:
            logger.error(f"Error downloading file stream from MinIO: {e}")
            return None

    def delete_file(self, object_key: str) -> bool:
        """
        Delete file from MinIO.

        Args:
            object_key: Object key to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.client.remove_object(self.bucket_name, object_key)
            logger.info(f"Deleted file from MinIO: {object_key}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {e}")
            return False

    def file_exists(self, object_key: str) -> bool:
        """Check if file exists in MinIO."""
        try:
            self.client.stat_object(self.bucket_name, object_key)
            return True
        except S3Error:
            return False


# Singleton instance
storage_service = StorageService()
