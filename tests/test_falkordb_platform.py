import importlib
import sys
import pytest
from pathlib import Path

# Add src to path for imports (needed for direct test execution)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Ensure minimal neo4j stub exists for import-time to avoid requiring the real neo4j package in tests
import types
sys.modules.setdefault('neo4j', types.SimpleNamespace(GraphDatabase=object, Driver=object))

from codegraphcontext.core import get_database_manager
from codegraphcontext.core.database_falkordb import FalkorDBManager


def test_falkordb_test_connection_reports_unsupported_on_windows(monkeypatch):
    # Simulate Windows platform
    monkeypatch.setattr(sys, 'platform', 'win32')
    ok, msg = FalkorDBManager.test_connection()
    assert ok is False
    assert msg is not None
    assert 'not supported on windows' in msg.lower()


def test_get_database_manager_explicit_falkor_on_windows_raises(monkeypatch):
    # Simulate Windows and explicit DATABASE_TYPE
    monkeypatch.setattr(sys, 'platform', 'win32')
    monkeypatch.setenv('DATABASE_TYPE', 'falkordb')

    with pytest.raises(ValueError) as exc:
        get_database_manager()
    assert 'not supported on windows' in str(exc.value).lower()


def test_import_core_does_not_fail_when_falkor_missing_on_windows(monkeypatch):
    # Ensure importing core module doesn't raise even if Falkor isn't available and we're on Windows
    monkeypatch.setattr(sys, 'platform', 'win32')
    # Reload module to simulate import-time behavior
    import codegraphcontext.core as core
    importlib.reload(core)
    # Should still have get_database_manager available
    assert hasattr(core, 'get_database_manager')
