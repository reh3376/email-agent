"""Attachment management system for email processing."""
from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Constants
DATE_DIR_PATTERN = "????-??-??"  # Pattern for date directories


class AttachmentStats(BaseModel):
    """Storage statistics for attachments."""
    
    totalFiles: int = Field(..., ge=0)
    totalSizeBytes: int = Field(..., ge=0)
    oldestFile: Optional[datetime] = None
    newestFile: Optional[datetime] = None
    byMimeType: Dict[str, int] = Field(default_factory=dict)
    byMessageId: Dict[str, int] = Field(default_factory=dict)


class AttachmentManager:
    """Manages email attachment storage and retrieval."""
    
    def __init__(self, base_path: str, retention_days: int = 90):
        """
        Initialize attachment manager.
        
        Args:
            base_path: Base directory for attachment storage
            retention_days: Number of days to retain attachments
        """
        self.base_path = Path(base_path).expanduser().resolve()
        self.retention_days = retention_days
        
        # Ensure base directory exists with proper permissions
        self.base_path.mkdir(parents=True, exist_ok=True)
        os.chmod(self.base_path, 0o700)  # User-only access
    
    def get_attachment_path(self, message_id: str, filename: str, date: Optional[datetime] = None) -> Path:
        """
        Get the storage path for an attachment.
        
        Args:
            message_id: Email message ID
            filename: Attachment filename
            date: Date for directory structure (defaults to today)
            
        Returns:
            Path where attachment should be stored
        """
        if date is None:
            date = datetime.now()
        
        # Sanitize inputs
        safe_message_id = "".join(c for c in message_id if c.isalnum() or c in "-_")
        safe_filename = Path(filename).name  # Get just the filename, no path components
        
        # Build path: base/YYYY-MM-DD/messageId/filename
        date_str = date.strftime("%Y-%m-%d")
        return self.base_path / date_str / safe_message_id / safe_filename
    
    def save_attachment(
        self,
        message_id: str,
        filename: str,
        content: bytes,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Save an attachment to storage.
        
        Args:
            message_id: Email message ID
            filename: Attachment filename
            content: Attachment content
            date: Date for directory structure
            
        Returns:
            Attachment metadata including storage path and hash
        """
        # Calculate hash
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Check for existing file with same hash (deduplication)
        existing_path = self._find_by_hash(sha256_hash)
        if existing_path:
            # File already exists, just return metadata
            return {
                "filename": filename,
                "storagePath": str(existing_path),
                "sha256Hash": sha256_hash,
                "size": len(content),
                "savedAt": datetime.now().isoformat(),
                "deduplicated": True
            }
        
        # Get storage path
        attachment_path = self.get_attachment_path(message_id, filename, date)
        
        # Create directory if needed
        attachment_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(attachment_path.parent, 0o700)
        
        # Save file
        attachment_path.write_bytes(content)
        os.chmod(attachment_path, 0o600)  # User read/write only
        
        return {
            "filename": filename,
            "storagePath": str(attachment_path),
            "sha256Hash": sha256_hash,
            "size": len(content),
            "savedAt": datetime.now().isoformat(),
            "deduplicated": False
        }
    
    def get_attachment(self, message_id: str, filename: str) -> Optional[bytes]:
        """
        Retrieve an attachment.
        
        Args:
            message_id: Email message ID
            filename: Attachment filename
            
        Returns:
            Attachment content or None if not found
        """
        # Try multiple date directories (last 7 days)
        for days_ago in range(7):
            date = datetime.now() - timedelta(days=days_ago)
            path = self.get_attachment_path(message_id, filename, date)
            if path.exists():
                return path.read_bytes()
        
        return None
    
    def delete_attachment(self, message_id: str, filename: str) -> bool:
        """
        Delete an attachment.
        
        Args:
            message_id: Email message ID
            filename: Attachment filename
            
        Returns:
            True if deleted, False if not found
        """
        # Try multiple date directories
        for days_ago in range(self.retention_days):
            date = datetime.now() - timedelta(days=days_ago)
            path = self.get_attachment_path(message_id, filename, date)
            if path.exists():
                path.unlink()
                # Remove empty directories
                try:
                    path.parent.rmdir()  # Remove message ID dir if empty
                    path.parent.parent.rmdir()  # Remove date dir if empty
                except OSError:
                    pass  # Directory not empty
                return True
        
        return False
    
    def list_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """
        List all attachments for a message.
        
        Args:
            message_id: Email message ID
            
        Returns:
            List of attachment metadata
        """
        attachments = []
        safe_message_id = "".join(c for c in message_id if c.isalnum() or c in "-_")
        
        # Search in all date directories
        for date_dir in self.base_path.glob(DATE_DIR_PATTERN):
            message_dir = date_dir / safe_message_id
            if message_dir.exists():
                for file_path in message_dir.iterdir():
                    if file_path.is_file():
                        stat = file_path.stat()
                        attachments.append({
                            "filename": file_path.name,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "path": str(file_path)
                        })
        
        return attachments
    
    def get_stats(self) -> AttachmentStats:
        """
        Get storage statistics.
        
        Returns:
            Attachment storage statistics
        """
        total_files = 0
        total_size = 0
        oldest_time = None
        newest_time = None
        by_mime_type: Dict[str, int] = {}
        by_message_id: Dict[str, int] = {}
        
        for date_dir in self.base_path.glob(DATE_DIR_PATTERN):
            for message_dir in date_dir.iterdir():
                if message_dir.is_dir():
                    message_id = message_dir.name
                    message_file_count = 0
                    
                    for file_path in message_dir.iterdir():
                        if file_path.is_file():
                            total_files += 1
                            message_file_count += 1
                            stat = file_path.stat()
                            total_size += stat.st_size
                            
                            # Track oldest/newest
                            mtime = datetime.fromtimestamp(stat.st_mtime)
                            if oldest_time is None or mtime < oldest_time:
                                oldest_time = mtime
                            if newest_time is None or mtime > newest_time:
                                newest_time = mtime
                            
                            # Guess MIME type from extension
                            ext = file_path.suffix.lower()
                            mime_type = self._guess_mime_type(ext)
                            by_mime_type[mime_type] = by_mime_type.get(mime_type, 0) + 1
                    
                    if message_file_count > 0:
                        by_message_id[message_id] = message_file_count
        
        return AttachmentStats(
            totalFiles=total_files,
            totalSizeBytes=total_size,
            oldestFile=oldest_time,
            newestFile=newest_time,
            byMimeType=by_mime_type,
            byMessageId=by_message_id
        )
    
    def cleanup_old_attachments(self) -> int:
        """
        Remove attachments older than retention period.
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for date_dir in self.base_path.glob(DATE_DIR_PATTERN):
            try:
                # Parse date from directory name
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff_date:
                    # Delete entire date directory
                    shutil.rmtree(date_dir)
                    deleted_count += sum(1 for _ in date_dir.rglob("*") if _.is_file())
            except (ValueError, OSError):
                continue
        
        return deleted_count
    
    def _find_by_hash(self, sha256_hash: str) -> Optional[Path]:
        """Find existing file by hash (for deduplication)."""
        # For now, simple implementation - could be optimized with a hash index
        for date_dir in self.base_path.glob(DATE_DIR_PATTERN):
            for message_dir in date_dir.iterdir():
                if message_dir.is_dir():
                    for file_path in message_dir.iterdir():
                        if file_path.is_file():
                            # Calculate hash of existing file
                            file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                            if file_hash == sha256_hash:
                                return file_path
        return None
    
    def _guess_mime_type(self, extension: str) -> str:
        """Guess MIME type from file extension."""
        mime_map = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".txt": "text/plain",
            ".zip": "application/zip",
            ".csv": "text/csv",
        }
        return mime_map.get(extension, "application/octet-stream")
