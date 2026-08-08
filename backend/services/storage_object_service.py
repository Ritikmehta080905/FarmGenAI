"""
backend/services/storage_object_service.py

MinIO / S3-compatible Object Storage Service — Section 14.
Manages crop image uploads, verification documents, and audit attachments.
"""

import os
import logging
import uuid
from typing import Dict, Any
from config.settings import settings

logger = logging.getLogger("ObjectStorageService")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")


class ObjectStorageService:
    """MinIO / Local File Storage Manager."""

    def __init__(self):
        self.minio_client = None
        self._init_client()

    def _init_client(self):
        try:
            from minio import Minio
            self.minio_client = Minio(
                endpoint=MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )
            logger.info(f"MinIO client connected to {MINIO_ENDPOINT}.")
        except Exception:
            logger.info("MinIO SDK not installed or server offline. Using local disk fallback for object storage.")

    def upload_file(self, bucket_name: str, file_name: str, file_data: bytes, content_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        Upload file data to bucket or local directory fallback.
        """
        file_id = f"file_{uuid.uuid4().hex[:8]}"

        if self.minio_client:
            try:
                import io
                # Ensure bucket exists
                found = self.minio_client.bucket_exists(bucket_name)
                if not found:
                    self.minio_client.make_bucket(bucket_name)

                data_stream = io.BytesIO(file_data)
                self.minio_client.put_object(
                    bucket_name,
                    file_name,
                    data_stream,
                    length=len(file_data),
                    content_type=content_type
                )
                url = f"http://{MINIO_ENDPOINT}/{bucket_name}/{file_name}"
                return {"success": True, "file_id": file_id, "url": url, "storage": "MinIO"}
            except Exception as e:
                logger.warning(f"MinIO upload error: {e}. Falling back to local storage.")

        # Local storage fallback
        local_dir = os.path.join("./node_storage/uploads", bucket_name)
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, file_name)

        with open(local_path, "wb") as f:
            f.write(file_data)

        return {
            "success": True,
            "file_id": file_id,
            "url": f"/static/uploads/{bucket_name}/{file_name}",
            "storage": "LocalDisk",
        }


# Singleton instance
object_storage_service = ObjectStorageService()
