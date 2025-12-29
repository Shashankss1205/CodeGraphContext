# src/codegraphcontext/core/__init__.py
"""
Core database management module.

Supports both Neo4j and FalkorDB Lite backends.
Use DATABASE_TYPE environment variable to switch:
- DATABASE_TYPE=falkordb - Uses embedded FalkorDB Lite (recommended for lite-version)
- DATABASE_TYPE=neo4j - Uses Neo4j server
- If not set, auto-detects based on what's available
"""
import os
from typing import Union

import importlib.util

def _is_falkordb_available() -> bool:
    """Check if FalkorDB Lite is installed (without importing native modules)."""
    try:
        # Check for redislite/falkordb-client spec without loading it
        return importlib.util.find_spec("redislite") is not None
    except ImportError:
        return False

def _is_neo4j_configured() -> bool:
    """Check if Neo4j is configured with credentials."""
    return all([
        os.getenv('NEO4J_URI'),
        os.getenv('NEO4J_USERNAME'),
        os.getenv('NEO4J_PASSWORD')
    ])

def get_database_manager() -> Union['DatabaseManager', 'FalkorDBManager']:
    """
    Factory function to get the appropriate database manager based on configuration.
    
    Selection logic:
    1. Runtime Override: 'CGC_RUNTIME_DB_TYPE' (set via --database flag)
    2. Configured Default: 'DEFAULT_DATABASE' (set via 'cgc default database')
    3. Legacy Env Var: 'DATABASE_TYPE'
    4. Implicit Default: FalkorDB (if available)
    5. Fallback: Neo4j (if configured)
    """
    from codegraphcontext.utils.debug_log import info_logger
    
    # 1. Runtime Override (CLI flag) or Config/Env
    db_type = os.getenv('CGC_RUNTIME_DB_TYPE')
    if not db_type:
        db_type = os.getenv('DEFAULT_DATABASE')
    if not db_type:
        db_type = os.getenv('DATABASE_TYPE')

    if db_type:
        db_type = db_type.lower()
        if db_type == 'falkordb':
            if not _is_falkordb_available():
                 raise ValueError("Database set to 'falkordb' but FalkorDB Lite is not installed.\nRun 'pip install falkordblite'")
            from .database_falkordb import FalkorDBManager
            info_logger("Using FalkorDB Lite (explicit)")
            return FalkorDBManager()
            
        elif db_type == 'neo4j':
            if not _is_neo4j_configured():
                 raise ValueError("Database set to 'neo4j' but it is not configured.\nRun 'cgc setup' to configure Neo4j.")
            from .database import DatabaseManager
            info_logger("Using Neo4j Server (explicit)")
            return DatabaseManager()
        else:
            raise ValueError(f"Unknown database type: '{db_type}'. Use 'falkordb' or 'neo4j'.")

    # 4. Implicit Default -> FalkorDB (Zero Config)
    if _is_falkordb_available():
        from .database_falkordb import FalkorDBManager
        info_logger("Using FalkorDB Lite (default)")
        return FalkorDBManager()
        
    # 5. Fallback if FalkorDB missing but Neo4j is ready
    if _is_neo4j_configured():
        from .database import DatabaseManager
        info_logger("Using Neo4j Server (auto-detected)")
        return DatabaseManager()

    raise ValueError(
        "No database backend available.\n"
        "Recommended: Install FalkorDB Lite ('pip install falkordblite')\n"
        "Alternative: Run 'cgc setup' to configure Neo4j."
    )

# For backward compatibility, export DatabaseManager
from .database import DatabaseManager
from .database_falkordb import FalkorDBManager

__all__ = ['DatabaseManager', 'FalkorDBManager', 'get_database_manager']
