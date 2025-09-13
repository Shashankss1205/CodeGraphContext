# src/codegraphcontext/tools/notebook_parser.py
import ast
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def debug_log(message):
    """Write debug message to a file"""
    debug_file = os.path.expanduser("~/mcp_debug.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(debug_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()


class NotebookParser:
    """Parser for Jupyter notebook files (.ipynb) that extracts Python code and converts it to a format suitable for the existing Python parser."""

    def __init__(self):
        self.temp_files = []  # Track temporary files for cleanup

    def parse_notebook(self, notebook_path: Path, imports_map: dict, is_dependency: bool = False) -> Dict:
        """
        Parse a Jupyter notebook file and extract Python code elements.
        
        Args:
            notebook_path: Path to the .ipynb file
            imports_map: Map of imports for resolution
            is_dependency: Whether this is a dependency file
            
        Returns:
            Dictionary containing parsed code elements similar to parse_python_file
        """
        debug_log(f"[parse_notebook] Starting parsing for: {notebook_path}")
        
        try:
            # Read and parse the notebook JSON
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)
            
            # Extract Python code from all code cells
            python_code = self._extract_python_code(notebook_data)
            
            if not python_code.strip():
                debug_log(f"[parse_notebook] No Python code found in: {notebook_path}")
                return {
                    "file_path": str(notebook_path),
                    "functions": [],
                    "classes": [],
                    "variables": [],
                    "imports": [],
                    "function_calls": [],
                    "is_dependency": is_dependency,
                    "notebook_cells": []
                }
            
            # Create a temporary Python file for parsing
            temp_python_file = self._create_temp_python_file(notebook_path, python_code)
            
            # Parse the temporary Python file using the existing AST parser
            parsed_data = self._parse_python_code(temp_python_file, notebook_path, imports_map, is_dependency)
            
            # Add notebook-specific metadata
            parsed_data["notebook_cells"] = self._extract_cell_metadata(notebook_data)
            parsed_data["original_notebook_path"] = str(notebook_path)
            
            debug_log(f"[parse_notebook] Successfully parsed notebook: {notebook_path}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing notebook {notebook_path}: {e}")
            debug_log(f"[parse_notebook] Error parsing {notebook_path}: {e}")
            return {"file_path": str(notebook_path), "error": str(e)}

    def _extract_python_code(self, notebook_data: dict) -> str:
        """
        Extract Python code from all code cells in the notebook.
        
        Args:
            notebook_data: Parsed JSON data from the notebook file
            
        Returns:
            Combined Python code from all code cells
        """
        python_lines = []
        cell_number = 0
        
        for cell in notebook_data.get('cells', []):
            if cell.get('cell_type') == 'code':
                cell_number += 1
                source = cell.get('source', [])
                
                # Handle both string and list source formats
                if isinstance(source, list):
                    cell_code = ''.join(source)
                else:
                    cell_code = source
                
                # Add cell marker comment for reference
                python_lines.append(f"# Cell {cell_number}")
                python_lines.append(cell_code)
                
                # Add spacing between cells
                if cell_code.strip():
                    python_lines.append("")
        
        return '\n'.join(python_lines)

    def _extract_cell_metadata(self, notebook_data: dict) -> List[Dict]:
        """
        Extract metadata about each cell in the notebook.
        
        Args:
            notebook_data: Parsed JSON data from the notebook file
            
        Returns:
            List of cell metadata dictionaries
        """
        cells_metadata = []
        
        for i, cell in enumerate(notebook_data.get('cells', [])):
            cell_info = {
                "cell_number": i + 1,
                "cell_type": cell.get('cell_type', 'unknown'),
                "execution_count": cell.get('execution_count'),
                "outputs": len(cell.get('outputs', [])),
                "source_lines": len(cell.get('source', [])) if isinstance(cell.get('source'), list) else 1
            }
            
            # Add source preview for code cells
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])
                if isinstance(source, list):
                    source_text = ''.join(source)
                else:
                    source_text = source
                
                # Get first few lines as preview
                preview_lines = source_text.split('\n')[:3]
                cell_info["source_preview"] = '\n'.join(preview_lines).strip()
            
            cells_metadata.append(cell_info)
        
        return cells_metadata

    def _create_temp_python_file(self, notebook_path: Path, python_code: str) -> Path:
        """
        Create a temporary Python file with the extracted code.
        
        Args:
            notebook_path: Original notebook path
            python_code: Extracted Python code
            
        Returns:
            Path to the temporary Python file
        """
        # Create a temporary file with .py extension
        temp_fd, temp_path = tempfile.mkstemp(suffix='.py', prefix=f'notebook_{notebook_path.stem}_')
        
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            temp_file_path = Path(temp_path)
            self.temp_files.append(temp_file_path)  # Track for cleanup
            debug_log(f"[parse_notebook] Created temp file: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            # Clean up the file descriptor if writing fails
            try:
                os.close(temp_fd)
            except:
                pass
            raise e

    def _parse_python_code(self, temp_python_file: Path, original_notebook_path: Path, imports_map: dict, is_dependency: bool) -> Dict:
        """
        Parse the temporary Python file using the existing AST parser.
        
        Args:
            temp_python_file: Path to the temporary Python file
            original_notebook_path: Path to the original notebook file
            imports_map: Map of imports for resolution
            is_dependency: Whether this is a dependency file
            
        Returns:
            Parsed code elements dictionary
        """
        try:
            with open(temp_python_file, "r", encoding="utf-8") as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            # Import the CodeVisitor from graph_builder
            from .graph_builder import CodeVisitor
            visitor = CodeVisitor(str(original_notebook_path), imports_map, is_dependency)
            visitor.visit(tree)
            
            return {
                "file_path": str(original_notebook_path),
                "functions": visitor.functions,
                "classes": visitor.classes,
                "variables": visitor.variables,
                "imports": visitor.imports,
                "function_calls": visitor.function_calls,
                "is_dependency": is_dependency,
            }
            
        except Exception as e:
            logger.error(f"Error parsing temporary Python file {temp_python_file}: {e}")
            raise e

    def cleanup_temp_files(self):
        """Clean up all temporary files created during parsing."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    debug_log(f"[parse_notebook] Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Could not clean up temp file {temp_file}: {e}")
        
        self.temp_files.clear()

    def is_notebook_file(self, file_path: Path) -> bool:
        """
        Check if a file is a Jupyter notebook.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file is a .ipynb file
        """
        return file_path.suffix.lower() == '.ipynb'

    def _extract_python_code_from_notebook(self, notebook_path: Path) -> str:
        """
        Extract Python code from a notebook file for pre-scanning.
        
        Args:
            notebook_path: Path to the notebook file
            
        Returns:
            Combined Python code from all code cells
        """
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)
            return self._extract_python_code(notebook_data)
        except Exception as e:
            logger.warning(f"Error extracting Python code from {notebook_path}: {e}")
            return ""

    def __del__(self):
        """Cleanup temporary files when the parser is destroyed."""
        self.cleanup_temp_files()
