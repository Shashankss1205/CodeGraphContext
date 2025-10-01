# src/codegraphcontext/tools/graph_builder.py
import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, Coroutine, Dict, Optional, Tuple
from datetime import datetime

import tree_sitter
from tree_sitter_css import language

from ..core.database import DatabaseManager
from ..core.jobs import JobManager, JobStatus
from ..utils.debug_log import debug_log

logger = logging.getLogger(__name__)

# This is for developers and testers only. It enables detailed debug logging to a file.
# Set to 1 to enable, 0 to disable.
debug_mode = 0

class CSSComplexityCalculator:
    """Calculates complexity metrics for CSS code."""
    def __init__(self):
        self.complexity = 1
        self.selector_count = 0
        self.property_count = 0
        self.rule_count = 0

    def calculate_complexity(self, css_content: str) -> Dict[str, int]:
        """Calculate various complexity metrics for CSS."""
        # Count selectors (basic complexity metric)
        selector_patterns = [
            r'[.#]?[a-zA-Z_-]+[^{]*{',  # Basic selectors
            r'@media\s+[^{]*{',         # Media queries
            r'@keyframes\s+[^{]*{',     # Keyframes
            r'@supports\s+[^{]*{',      # Feature queries
        ]
        
        for pattern in selector_patterns:
            matches = re.findall(pattern, css_content)
            self.selector_count += len(matches)
        
        # Count CSS properties
        property_pattern = r'[a-zA-Z-]+\s*:'
        self.property_count = len(re.findall(property_pattern, css_content))
        
        # Count CSS rules (blocks with properties)
        rule_pattern = r'[^{]*{[^}]*}'
        self.rule_count = len(re.findall(rule_pattern, css_content))
        
        # Overall complexity based on selectors and nesting
        self.complexity = self.selector_count + (self.property_count // 10)
        
        return {
            'complexity': self.complexity,
            'selector_count': self.selector_count,
            'property_count': self.property_count,
            'rule_count': self.rule_count
        }


class CSSVisitor:
    """
    CSS AST visitor that extracts CSS rules, selectors, properties, and at-rules.
    """

    def __init__(self, file_path: str, imports_map: dict, is_dependency: bool = False):
        self.file_path = file_path
        self.is_dependency = is_dependency
        self.imports_map = imports_map
        self.selectors, self.properties, self.rules, self.at_rules, self.media_queries = [], [], [], [], []
        self.complexity_calculator = CSSComplexityCalculator()
        
        # CSS-specific data structures
        self.selector_table = {}
        self.property_table = {}
        self.rule_table = {}

    def visit_css_tree(self, tree, source_code: str):
        """Visit the CSS AST tree and extract CSS elements."""
        self.source_code = source_code
        self._traverse_node(tree.root_node)
        
    def _traverse_node(self, node, depth=0):
        """Recursively traverse CSS AST nodes."""
        if not node:
            return
            
        node_type = node.type
        node_text = self.source_code[node.start_byte:node.end_byte] if hasattr(self, 'source_code') else ""
        
        # Handle different CSS node types
        if node_type == "rule_set":
            self._extract_rule_set(node, node_text)
        elif node_type == "at_rule":
            self._extract_at_rule(node, node_text)
        elif node_type == "media_query":
            self._extract_media_query(node, node_text)
        elif node_type == "keyframes":
            self._extract_keyframes(node, node_text)
        elif node_type == "import":
            self._extract_import(node, node_text)
        elif node_type == "namespace":
            self._extract_namespace(node, node_text)
        
        # Recursively traverse child nodes
        for child in node.children:
            self._traverse_node(child, depth + 1)
    
    def _extract_rule_set(self, node, node_text: str):
        """Extract CSS rule set (selector + properties)."""
        selectors = []
        properties = []
        
        for child in node.children:
            if child.type == "selectors":
                selector_text = self.source_code[child.start_byte:child.end_byte]
                selectors.append(selector_text.strip())
            elif child.type == "block":
                properties = self._extract_properties_from_block(child)
        
        # Create rule data
        rule_data = {
            "selectors": selectors,
            "properties": properties,
            "line_number": node.start_point[0] + 1,
            "source": node_text.strip(),
            "selector_text": ", ".join(selectors),
            "property_count": len(properties)
        }
        
        self.rules.append(rule_data)
        
        # Add to selector table
        for selector in selectors:
            self.selector_table[selector] = rule_data
    
    def _extract_properties_from_block(self, block_node):
        """Extract CSS properties from a block node."""
        properties = []
        
        for child in block_node.children:
            if child.type == "declaration":
                prop_text = self.source_code[child.start_byte:child.end_byte]
                property_name = ""
                property_value = ""
                
                for prop_child in child.children:
                    if prop_child.type == "property_name":
                        property_name = self.source_code[prop_child.start_byte:prop_child.end_byte]
                    elif prop_child.type == "property_value":
                        property_value = self.source_code[prop_child.start_byte:prop_child.end_byte]
                
                prop_data = {
                    "name": property_name.strip(),
                    "value": property_value.strip(),
                    "line_number": child.start_point[0] + 1,
                    "source": prop_text.strip()
                }
                
                properties.append(prop_data)
                self.properties.append(prop_data)
                
                # Add to property table
                if property_name:
                    self.property_table[property_name] = prop_data
        
        return properties
    
    def _extract_at_rule(self, node, node_text: str):
        """Extract CSS at-rule (e.g., @media, @keyframes)."""
        at_rule_data = {
            "type": "at_rule",
            "name": "",
            "content": node_text.strip(),
            "line_number": node.start_point[0] + 1,
            "source": node_text.strip()
        }
        
        for child in node.children:
            if child.type == "at_keyword":
                at_rule_data["name"] = self.source_code[child.start_byte:child.end_byte].replace("@", "")
        
        self.at_rules.append(at_rule_data)
    
    def _extract_media_query(self, node, node_text: str):
        """Extract CSS media query."""
        media_data = {
            "type": "media_query",
            "query": "",
            "content": node_text.strip(),
            "line_number": node.start_point[0] + 1,
            "source": node_text.strip()
        }
        
        for child in node.children:
            if child.type == "media_query_list":
                media_data["query"] = self.source_code[child.start_byte:child.end_byte]
        
        self.media_queries.append(media_data)
    
    def _extract_keyframes(self, node, node_text: str):
        """Extract CSS keyframes animation."""
        keyframes_data = {
            "type": "keyframes",
            "name": "",
            "content": node_text.strip(),
            "line_number": node.start_point[0] + 1,
            "source": node_text.strip()
        }
        
        for child in node.children:
            if child.type == "keyframes_name":
                keyframes_data["name"] = self.source_code[child.start_byte:child.end_byte]
        
        self.at_rules.append(keyframes_data)
    
    def _extract_import(self, node, node_text: str):
        """Extract CSS import statement."""
        import_data = {
            "type": "import",
            "url": "",
            "content": node_text.strip(),
            "line_number": node.start_point[0] + 1,
            "source": node_text.strip()
        }
        
        for child in node.children:
            if child.type == "string_value":
                import_data["url"] = self.source_code[child.start_byte:child.end_byte].strip('"\'')
        
        self.at_rules.append(import_data)
    
    def _extract_namespace(self, node, node_text: str):
        """Extract CSS namespace declaration."""
        namespace_data = {
            "type": "namespace",
            "prefix": "",
            "url": "",
            "content": node_text.strip(),
            "line_number": node.start_point[0] + 1,
            "source": node_text.strip()
        }
        
        for child in node.children:
            if child.type == "namespace_prefix":
                namespace_data["prefix"] = self.source_code[child.start_byte:child.end_byte]
            elif child.type == "string_value":
                namespace_data["url"] = self.source_code[child.start_byte:child.end_byte].strip('"\'')
        
        self.at_rules.append(namespace_data)


class GraphBuilder:
    """Module for building and managing the Neo4j CSS graph."""

    def __init__(self, db_manager: DatabaseManager, job_manager: JobManager, loop: asyncio.AbstractEventLoop):
        self.db_manager = db_manager
        self.job_manager = job_manager
        self.loop = loop  # Store the main event loop
        self.driver = self.db_manager.get_driver()
        self.create_schema()

    def create_schema(self):
        """Create constraints and indexes in Neo4j for CSS elements."""
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT repository_path IF NOT EXISTS FOR (r:Repository) REQUIRE r.path IS UNIQUE")
                session.run("CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
                session.run("CREATE CONSTRAINT directory_path IF NOT EXISTS FOR (d:Directory) REQUIRE d.path IS UNIQUE")
                session.run("CREATE CONSTRAINT css_rule_unique IF NOT EXISTS FOR (r:CSSRule) REQUIRE (r.selector_text, r.file_path, r.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT css_selector_unique IF NOT EXISTS FOR (s:CSSSelector) REQUIRE (s.name, s.file_path, s.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT css_property_unique IF NOT EXISTS FOR (p:CSSProperty) REQUIRE (p.name, p.file_path, p.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT css_at_rule_unique IF NOT EXISTS FOR (a:CSSAtRule) REQUIRE (a.name, a.file_path, a.line_number) IS UNIQUE")
                
                # Create a full-text search index for CSS search
                session.run("""
                    CREATE FULLTEXT INDEX css_search_index IF NOT EXISTS 
                    FOR (n:CSSRule|CSSSelector|CSSProperty|CSSAtRule) 
                    ON EACH [n.name, n.source, n.selector_text, n.property_value]
                """)
                
                logger.info("CSS database schema verified/created successfully")
            except Exception as e:
                logger.warning(f"CSS schema creation warning: {e}")

    def _pre_scan_for_imports(self, files: list[Path]) -> dict:
        """Pre-scan CSS files to find @import statements."""
        imports_map = {}
        
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Find @import statements
                import_pattern = r'@import\s+["\']([^"\']+)["\']'
                imports = re.findall(import_pattern, content)
                
                if imports:
                    imports_map[str(file_path)] = imports
                    
            except Exception as e:
                logger.warning(f"Could not pre-scan {file_path}: {e}")
                
        return imports_map

    def estimate_processing_time(self, path: Path) -> Optional[Tuple[int, float]]:
        """Estimate processing time and file count for CSS files."""
        try:
            if path.is_file():
                files = [path]
            else:
                files = list(path.rglob("*.css"))
            
            total_files = len(files)
            # Simple heuristic: 0.1 seconds per file
            estimated_time = total_files * 0.1
            return total_files, estimated_time
        except Exception as e:
            logger.error(f"Could not estimate processing time for {path}: {e}")
            return None

    async def build_graph_from_path_async(
        self, path: Path, is_dependency: bool = False, job_id: str = None
    ):
        """Build the CSS graph from a given path asynchronously."""
        try:
            debug_log(f"[build_graph_from_path_async] Starting async processing for: {path}")
            
            # Update job status to running
            if job_id:
                self.job_manager.update_job(job_id, status=JobStatus.RUNNING, start_time=datetime.now())
            
            # Get all CSS files
            if path.is_file():
                css_files = [path]
            else:
                css_files = list(path.rglob("*.css"))
            
            if not css_files:
                logger.warning(f"No CSS files found in {path}")
                if job_id:
                    self.job_manager.update_job(job_id, status=JobStatus.COMPLETED, end_time=datetime.now())
                return
            
            # Pre-scan for imports
            imports_map = self._pre_scan_for_imports(css_files)
            
            # Process each CSS file
            processed_files = 0
            total_files = len(css_files)
            
            for css_file in css_files:
                try:
                    # Parse the CSS file
                    parsed_data = self.parse_css_file(path, css_file, imports_map, is_dependency)
                    
                    if "error" not in parsed_data:
                        # Add to Neo4j
                        await self._add_css_to_graph(parsed_data)
                        processed_files += 1
                        
                        # Update progress
                        if job_id:
                            progress = (processed_files / total_files) * 100
                            self.job_manager.update_job(job_id, progress=progress, files_processed=processed_files)
                    
                except Exception as e:
                    logger.error(f"Error processing {css_file}: {e}")
                    debug_log(f"[build_graph_from_path_async] Error processing {css_file}: {e}")
            
            # Mark job as completed
            if job_id:
                self.job_manager.update_job(
                    job_id, 
                    status=JobStatus.COMPLETED, 
                    end_time=datetime.now(),
                    files_processed=processed_files,
                    total_files=total_files
                )
            
            debug_log(f"[build_graph_from_path_async] Completed processing {processed_files}/{total_files} files from {path}")
            
        except Exception as e:
            logger.error(f"Error in build_graph_from_path_async: {e}")
            debug_log(f"[build_graph_from_path_async] Error: {e}")
            if job_id:
                self.job_manager.update_job(job_id, status=JobStatus.FAILED, end_time=datetime.now())

    def parse_css_file(self, repo_path: Path, file_path: Path, imports_map: dict, is_dependency: bool = False) -> Dict:
        """Parse a CSS file and extract CSS elements using tree-sitter."""
        debug_log(f"[parse_css_file] Starting parsing for: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            
            # Create CSS parser
            parser = tree_sitter.Parser()
            parser.set_language(language())
            
            # Parse the CSS
            tree = parser.parse(bytes(source_code, "utf8"))
            
            # Visit the tree
            visitor = CSSVisitor(str(file_path), imports_map, is_dependency)
            visitor.visit_css_tree(tree, source_code)
            
            # Calculate complexity
            complexity_metrics = visitor.complexity_calculator.calculate_complexity(source_code)
            
            if debug_mode:
                debug_log(f"[parse_css_file] Successfully parsed: {file_path}")
                
            return {
                "repo_path": str(repo_path),
                "file_path": str(file_path),
                "selectors": visitor.selectors,
                "properties": visitor.properties,
                "rules": visitor.rules,
                "at_rules": visitor.at_rules,
                "media_queries": visitor.media_queries,
                "complexity_metrics": complexity_metrics,
                "is_dependency": is_dependency,
            }
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            debug_log(f"[parse_css_file] Error parsing {file_path}: {e}")
            return {"file_path": str(file_path), "error": str(e)}

    async def _add_css_to_graph(self, parsed_data: Dict):
        """Add parsed CSS data to the Neo4j graph."""
        try:
            with self.driver.session() as session:
                # Create or update repository node
                session.run("""
                    MERGE (r:Repository {path: $repo_path})
                    SET r.last_updated = datetime()
                """, repo_path=parsed_data["repo_path"])
                
                # Create file node
                session.run("""
                    MERGE (f:File {path: $file_path})
                    SET f.repository_path = $repo_path,
                        f.is_dependency = $is_dependency,
                        f.last_updated = datetime(),
                        f.complexity = $complexity,
                        f.selector_count = $selector_count,
                        f.property_count = $property_count,
                        f.rule_count = $rule_count
                """, 
                file_path=parsed_data["file_path"],
                repo_path=parsed_data["repo_path"],
                is_dependency=parsed_data["is_dependency"],
                complexity=parsed_data["complexity_metrics"]["complexity"],
                selector_count=parsed_data["complexity_metrics"]["selector_count"],
                property_count=parsed_data["complexity_metrics"]["property_count"],
                rule_count=parsed_data["complexity_metrics"]["rule_count"])
                
                # Create CSS rules
                for rule in parsed_data["rules"]:
                    session.run("""
                        MERGE (rule:CSSRule {
                            selector_text: $selector_text,
                            file_path: $file_path,
                            line_number: $line_number
                        })
                        SET rule.source = $source,
                            rule.property_count = $property_count,
                            rule.last_updated = datetime()
                        
                        MERGE (f:File {path: $file_path})
                        MERGE (f)-[:CONTAINS]->(rule)
                    """,
                    selector_text=rule["selector_text"],
                    file_path=parsed_data["file_path"],
                    line_number=rule["line_number"],
                    source=rule["source"],
                    property_count=rule["property_count"])
                    
                    # Create selectors
                    for selector in rule["selectors"]:
                        session.run("""
                            MERGE (sel:CSSSelector {
                                name: $name,
                                file_path: $file_path,
                                line_number: $line_number
                            })
                            SET sel.source = $source,
                                sel.last_updated = datetime()
                            
                            MERGE (rule:CSSRule {
                                selector_text: $selector_text,
                                file_path: $file_path,
                                line_number: $line_number
                            })
                            MERGE (sel)-[:PART_OF]->(rule)
                        """,
                        name=selector,
                        file_path=parsed_data["file_path"],
                        line_number=rule["line_number"],
                        source=selector,
                        selector_text=rule["selector_text"])
                
                # Create CSS properties
                for prop in parsed_data["properties"]:
                    session.run("""
                        MERGE (prop:CSSProperty {
                            name: $name,
                            file_path: $file_path,
                            line_number: $line_number
                        })
                        SET prop.value = $value,
                            prop.source = $source,
                            prop.last_updated = datetime()
                        
                        MERGE (f:File {path: $file_path})
                        MERGE (f)-[:CONTAINS]->(prop)
                    """,
                    name=prop["name"],
                    file_path=parsed_data["file_path"],
                    line_number=prop["line_number"],
                    value=prop["value"],
                    source=prop["source"])
                
                # Create at-rules
                for at_rule in parsed_data["at_rules"]:
                    session.run("""
                        MERGE (at:CSSAtRule {
                            name: $name,
                            file_path: $file_path,
                            line_number: $line_number
                        })
                        SET at.type = $type,
                            at.content = $content,
                            at.source = $source,
                            at.last_updated = datetime()
                        
                        MERGE (f:File {path: $file_path})
                        MERGE (f)-[:CONTAINS]->(at)
                    """,
                    name=at_rule.get("name", ""),
                    file_path=parsed_data["file_path"],
                    line_number=at_rule["line_number"],
                    type=at_rule["type"],
                    content=at_rule["content"],
                    source=at_rule["source"])
                
        except Exception as e:
            logger.error(f"Error adding CSS to graph: {e}")
            debug_log(f"[_add_css_to_graph] Error: {e}")

    def delete_repository_from_graph(self, repo_path: str):
        """Delete a repository and all its CSS files from the graph."""
        try:
            with self.driver.session() as session:
                # Delete all nodes related to this repository
                session.run("""
                    MATCH (r:Repository {path: $repo_path})
                    OPTIONAL MATCH (r)<-[:CONTAINS]-(f:File)
                    OPTIONAL MATCH (f)-[:CONTAINS]->(n)
                    DETACH DELETE r, f, n
                """, repo_path=repo_path)
                
                logger.info(f"Deleted repository {repo_path} from CSS graph")
        except Exception as e:
            logger.error(f"Error deleting repository {repo_path}: {e}")

    def update_file_in_graph(self, file_path: Path, repo_path: Path, imports_map: dict):
        """Update a single CSS file in the graph."""
        try:
            file_path_str = str(file_path)
            
            # Parse the updated file
            parsed_data = self.parse_css_file(repo_path, file_path, imports_map)
            
            if "error" in parsed_data:
                logger.error(f"Error parsing updated file {file_path}: {parsed_data['error']}")
                return {"error": parsed_data["error"], "path": file_path_str}
            
            # Remove old data for this file
            with self.driver.session() as session:
                session.run("""
                    MATCH (f:File {path: $file_path})
                    OPTIONAL MATCH (f)-[:CONTAINS]->(n)
                    DETACH DELETE n
                """, file_path=file_path_str)
            
            # Add updated data
            asyncio.create_task(self._add_css_to_graph(parsed_data))
            
            return {"updated": True, "path": file_path_str}
            
        except Exception as e:
            logger.error(f"Error updating file {file_path}: {e}")
            return {"error": str(e), "path": str(file_path)}

    def remove_file_from_graph(self, file_path: Path):
        """Remove a CSS file from the graph."""
        try:
            file_path_str = str(file_path)
            
            with self.driver.session() as session:
                session.run("""
                    MATCH (f:File {path: $file_path})
                    OPTIONAL MATCH (f)-[:CONTAINS]->(n)
                    DETACH DELETE f, n
                """, file_path=file_path_str)
            
            return {"deleted": True, "path": file_path_str}
            
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")
            return {"error": str(e), "path": str(file_path)}
