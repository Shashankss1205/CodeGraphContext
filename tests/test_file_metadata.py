"""
Tests for file metadata utilities.
"""

import pytest
import tempfile
import time
from pathlib import Path
from codegraphcontext.core.file_metadata import (
    FileMetadata,
    compute_file_hash,
    get_file_metadata,
    has_file_changed
)


def test_compute_file_hash():
    """Test that identical files produce identical hashes"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello World")
        path1 = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello World")
        path2 = f.name
    
    hash1 = compute_file_hash(path1)
    hash2 = compute_file_hash(path2)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
    
    # Cleanup
    Path(path1).unlink()
    Path(path2).unlink()


def test_get_file_metadata():
    """Test extracting metadata from a file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test content")
        path = f.name
    
    metadata = get_file_metadata(path)
    
    assert metadata is not None
    assert metadata.path.endswith(path)
    assert metadata.size > 0
    assert metadata.content_hash != ""
    assert metadata.last_modified > 0
    
    Path(path).unlink()


def test_has_file_changed_new_file():
    """Test detecting a new file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("New file")
        path = f.name
    
    # No stored metadata = new file
    changed, reason = has_file_changed(path, None)
    
    assert changed is True
    assert reason == "new_file"
    
    Path(path).unlink()


def test_has_file_changed_content_changed():
    """Test detecting content change"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Original content")
        path = f.name
    
    # Get initial metadata
    initial_metadata = get_file_metadata(path).to_dict()
    
    # Wait a bit and modify file
    time.sleep(0.1)
    with open(path, 'w') as f:
        f.write("Modified content")
    
    # Check if changed
    changed, reason = has_file_changed(path, initial_metadata)
    
    assert changed is True
    assert reason in ["size_changed", "content_changed"]
    
    Path(path).unlink()


def test_has_file_changed_unchanged():
    """Test detecting unchanged file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Static content")
        path = f.name
    
    # Get metadata
    metadata = get_file_metadata(path).to_dict()
    
    # Check immediately - should be unchanged
    changed, reason = has_file_changed(path, metadata)
    
    assert changed is False
    assert reason == "unchanged"
    
    Path(path).unlink()
