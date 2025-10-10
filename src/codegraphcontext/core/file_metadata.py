# this will handle the metadata utilities for files for incremental INDEXING
# will include functions to read, write, and update metadata such as last modified time, file size, and hash values.

import os
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FileMetadata:
    """
    Represents file metadata for change detection.
    Attributes:
        path: Absolute file path
        content_hash: SHA-256 hash of file content
        last_modified: File modification timestamp (Unix time)
        size: File size in bytes
        last_indexed: When we last indexed this file
        parser_version: Version of parser used
    """
    path: str
    content_hash: str
    last_modified: float
    size: int
    last_indexed: float
    parser_version: str = "1.0.0"  
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Neo4j storage."""
        return {
            'path': self.path,
            'content_hash': self.content_hash,
            'last_modified': self.last_modified,
            'size': self.size,
            'last_indexed': self.last_indexed,
            'parser_version': self.parser_version
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FileMetadata':
        """Create from Neo4j node properties."""
        return cls(
            path=data['path'],
            content_hash=data.get('content_hash', ''),
            last_modified=data.get('last_modified', 0.0),
            size=data.get('size', 0),
            last_indexed=data.get('last_indexed', 0.0),
            parser_version=data.get('parser_version', '1.0.0')
        )


def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of file content.
    Args:
        file_path: Path to file
    Returns:
        SHA-256 hash as hex string 
    """
    sha256_hash = hashlib.sha256()
    
    try:
        # Read file in chunks to handle large files
        with open(file_path, "rb") as f:
            # Read 64KB at a time
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""


def get_file_metadata(file_path: str) -> Optional[FileMetadata]:
    """
    Get current metadata for a file from the file system.
    This reads the ACTUAL current state of the file,
    not what's stored in the database.
    
    Args:
        file_path: Path to file
    Returns:
        FileMetadata object or None if file doesn't exist
    """
    try:
        # Get file stats (size, timestamps, etc.)
        stat = os.stat(file_path)
        
        # Compute content hash
        content_hash = compute_file_hash(file_path)
        
        # Create metadata object
        metadata = FileMetadata(
            path=str(Path(file_path).resolve()),  # Absolute path
            content_hash=content_hash,
            last_modified=stat.st_mtime,  # Modification time
            size=stat.st_size,  # File size in bytes
            last_indexed=time.time()  # Current time (when we're checking)
        )
        
        return metadata
    
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error getting metadata for {file_path}: {e}")
        return None


def has_file_changed(
    file_path: str, 
    stored_metadata: Optional[Dict]
) -> Tuple[bool, str]:
    """
    Detect if a file has changed since last indexing.
    Uses multi-level detection for optimal performance:
    1. Check size (instant)
    2. Check timestamp (instant)
    3. Check content hash (slow but accurate)
    
    Args:
        file_path: Path to file
        stored_metadata: Metadata from database (or None if new file)
    Returns:
        Tuple of (has_changed: bool, reason: str)
        Reasons: "new_file", "size_changed", "content_changed", 
                    "timestamp_only", "parser_upgraded", "unchanged"
    """
    # If no stored metadata, it's a new file
    if not stored_metadata:
        return True, "new_file"
    
    try:
        # Get current file state
        current_stat = os.stat(file_path)
        
        # LEVEL 1: Quick size check (instant)
        if current_stat.st_size != stored_metadata.get('size', 0):
            logger.debug(f"{file_path}: Size changed")
            return True, "size_changed"
        
        # LEVEL 2: Timestamp check (instant)
        stored_mtime = stored_metadata.get('last_modified', 0)
        if current_stat.st_mtime > stored_mtime:
            # Timestamp changed - verify with hash
            logger.debug(f"{file_path}: Timestamp changed, verifying content...")
            
            # LEVEL 3: Content hash (slow but accurate)
            current_hash = compute_file_hash(file_path)
            stored_hash = stored_metadata.get('content_hash', '')
            
            if current_hash != stored_hash:
                logger.debug(f"{file_path}: Content changed")
                return True, "content_changed"
            else:
                # False positive - timestamp changed but content didn't
                # (e.g., file was touched but not modified)
                logger.debug(f"{file_path}: Timestamp changed but content unchanged")
                return False, "timestamp_only"
        
        # LEVEL 4: Check parser version
        # If we upgraded the parser, we should re-index
        current_parser_version = "1.0.0"
        stored_parser_version = stored_metadata.get('parser_version', '1.0.0')
        
        if stored_parser_version < current_parser_version:
            logger.debug(f"{file_path}: Parser upgraded")
            return True, "parser_upgraded"
        
        # No changes detected
        return False, "unchanged"
    
    except FileNotFoundError:
        # File was deleted
        return True, "file_deleted"
    except Exception as e:
        logger.error(f"Error checking {file_path}: {e}")
        # When in doubt, assume it changed
        return True, "error_checking"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Example:
        >>> format_file_size(1024)
        "1.00 KB"
        >>> format_file_size(1048576)
        "1.00 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
