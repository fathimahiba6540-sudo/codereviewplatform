import os
import zipfile
import shutil
from typing import Tuple
from backend.app.core.exceptions import AppException


class ZipService:
    """Service for handling secure ZIP file validation and extraction."""

    MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

    @classmethod
    def validate_zip_header(cls, file_path: str) -> bool:
        """Validate ZIP file magic header bytes (PK\x03\x04)."""
        if not os.path.exists(file_path):
            return False
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"PK\x03\x04"

    @classmethod
    def is_safe_path(cls, base_dir: str, target_path: str) -> bool:
        """Prevent Zip Slip vulnerability by ensuring target path resides inside base_dir."""
        base_dir_abs = os.path.abspath(base_dir)
        target_path_abs = os.path.abspath(target_path)
        return os.path.commonpath([base_dir_abs]) == os.path.commonpath([base_dir_abs, target_path_abs])

    @classmethod
    def extract_zip(cls, zip_file_path: str, extract_to_dir: str) -> Tuple[bool, str]:
        """Extract ZIP archive safely into extract_to_dir."""
        if not zipfile.is_zipfile(zip_file_path):
            raise AppException(message="Invalid or corrupt ZIP file archive", code="INVALID_ZIP")

        # Check total extracted size limit
        total_uncompressed_bytes = 0
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            for member in zip_ref.infolist():
                total_uncompressed_bytes += member.file_size
                if total_uncompressed_bytes > cls.MAX_SIZE_BYTES:
                    raise AppException(
                        message=f"ZIP extracted content exceeds maximum limit of {cls.MAX_SIZE_BYTES // (1024 * 1024)} MB",
                        code="ZIP_TOO_LARGE"
                    )

            os.makedirs(extract_to_dir, exist_ok=True)

            # Safely extract members
            for member in zip_ref.infolist():
                target_path = os.path.join(extract_to_dir, member.filename)
                if not cls.is_safe_path(extract_to_dir, target_path):
                    raise AppException(
                        message="Potential Zip Slip path traversal security risk detected in archive",
                        code="SECURITY_VIOLATION"
                    )
                zip_ref.extract(member, extract_to_dir)

        return True, extract_to_dir
