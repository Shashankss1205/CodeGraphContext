
# src/codegraphcontext/tools/graph_builder.py
import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Coroutine, Dict, Optional, Tuple
from datetime import datetime

from ..core.database import DatabaseManager
from ..core.jobs import JobManager, JobStatus
from ..utils.debug_log import debug_log

# New imports for tree-sitter
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language

logger = logging.getLogger(__name__)

# This is for developers and testers only. It enables detailed debug logging to a file.
# Set to 1 to enable, 0 to disable.
debug_mode = 0


class TreeSitterParser:
    """A generic parser wrapper for a specific language using tree-sitter."""

    def __init__(self, language_name: str):
        self.language_name = language_name
        self.language: Language = get_language(language_name)
        self.parser = Parser()
        self.parser.set_language(self.language)

        self.language_specific_parser = None
        if self.language_name == 'css':
            from .languages.css import CSSTreeSitterParser
            self.language_specific_parser = CSSTreeSitterParser(self)

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict:
        """Dispatches parsing to the language-specific parser."""
        if self.language_specific_parser:
            return self.language_specific_parser.parse(file_path, is_dependency)
        else:
            raise NotImplementedError(f"No language-specific parser implemented for {self.language_name}")

class GraphBuilder:
    """Module for building and managing the Neo4j code graph."""

    def __init__(self, db_manager: DatabaseManager, job_manager: JobManager, loop: asyncio.AbstractEventLoop):
        self.db_manager = db_manager
        self.job_manager = job_manager
        self.loop = loop
        self.driver = self.db_manager.get_driver()
        self.parsers = {
            '.css': TreeSitterParser('css'),
        }
        self.create_schema()

    # A general schema creation based on common features across languages
    def create_schema(self):
        """Create constraints and indexes in Neo4j."""
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT repository_path IF NOT EXISTS FOR (r:Repository) REQUIRE r.path IS UNIQUE")
                session.run("CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
                session.run("CREATE CONSTRAINT directory_path IF NOT EXISTS FOR (d:Directory) REQUIRE d.path IS UNIQUE")
                session.run("CREATE CONSTRAINT function_unique IF NOT EXISTS FOR (f:Function) REQUIRE (f.name, f.file_path, f.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT class_unique IF NOT EXISTS FOR (c:Class) REQUIRE (c.name, c.file_path, c.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT variable_unique IF NOT EXISTS FOR (v:Variable) REQUIRE (v.name, v.file_path, v.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT module_name IF NOT EXISTS FOR (m:Module) REQUIRE m.name IS UNIQUE")

                # Indexes for language attribute
                session.run("CREATE INDEX function_lang IF NOT EXISTS FOR (f:Function) ON (f.lang)")
                session.run("CREATE INDEX class_lang IF NOT EXISTS FOR (c:Class) ON (c.lang)")
                
                session.run("""
                    CREATE FULLTEXT INDEX code_search_index IF NOT EXISTS 
                    FOR (n:Function|Class|Variable) 
                    ON EACH [n.name, n.source, n.docstring]
                """ )
                
                logger.info("Database schema verified/created successfully")
            except Exception as e:
                logger.warning(f"Schema creation warning: {e}")


    def _pre_scan_for_imports(self, files: list[Path]) -> dict:
        """Dispatches pre-scan to the correct language-specific implementation."""
        imports_map = {}
        
        # Group files by language/extension
        files_by_lang = {}
        for file in files:
            if file.suffix in self.parsers:
                lang_ext = file.suffix
                if lang_ext not in files_by_lang:
                    files_by_lang[lang_ext] = []
                files_by_lang[lang_ext].append(file)

        if '.css' in files_by_lang:
            from .languages import css as css_lang_module
            imports_map.update(css_lang_module.pre_scan_css(files_by_lang['.css'], self.parsers['.css']))
            
        return imports_map

    # Language-agnostic method
    def add_repository_to_graph(self, repo_path: Path, is_dependency: bool = False):
        """Adds a repository node using its absolute path as the unique key."""
        repo_name = repo_path.name
        repo_path_str = str(repo_path.resolve())
        with self.driver.session() as session:
            session.run(
                """
                MERGE (r:Repository {path: $path})
                SET r.name = $name, r.is_dependency = $is_dependency
                """,
                path=repo_path_str,
                name=repo_name,
                is_dependency=is_dependency,
            )

    # First pass to add file and its contents
    def add_file_to_graph(self, file_data: Dict, repo_name: str, imports_map: dict):
        logger.info("Executing add_file_to_graph with my change!")
        """Adds a file and its contents within a single, unified session."""
        file_path_str = str(Path(file_data['file_path']).resolve())
        file_name = Path(file_path_str).name
        is_dependency = file_data.get('is_dependency', False)

        with self.driver.session() as session:
            try:
                # Match repository by path, not name, to avoid conflicts with same-named folders at different locations
                repo_result = session.run("MATCH (r:Repository {path: $repo_path}) RETURN r.path as path", repo_path=str(Path(file_data['repo_path']).resolve())).single()
                relative_path = str(Path(file_path_str).relative_to(Path(repo_result['path']))) if repo_result else file_name
            except ValueError:
                relative_path = file_name

            session.run("""
                MERGE (f:File {path: $path})
                SET f.name = $name, f.relative_path = $relative_path, f.is_dependency = $is_dependency
            """, path=file_path_str, name=file_name, relative_path=relative_path, is_dependency=is_dependency)

            file_path_obj = Path(file_path_str)
            repo_path_obj = Path(repo_result['path'])
            
            relative_path_to_file = file_path_obj.relative_to(repo_path_obj)
            
            parent_path = str(repo_path_obj)
            parent_label = 'Repository'

            for part in relative_path_to_file.parts[:-1]:
                current_path = Path(parent_path) / part
                current_path_str = str(current_path)
                
                session.run(f"""
                    MATCH (p:{parent_label} {{path: $parent_path}})
                    MERGE (d:Directory {{path: $current_path}})
                    SET d.name = $part
                    MERGE (p)-[:CONTAINS]->(d)
                """, parent_path=parent_path, current_path=current_path_str, part=part)

                parent_path = current_path_str
                parent_label = 'Directory'

            session.run(f"""
                MATCH (p:{parent_label} {{path: $parent_path}})
                MATCH (f:File {{path: $file_path}})
                MERGE (p)-[:CONTAINS]->(f)
            """, parent_path=parent_path, file_path=file_path_str)

            # CONTAINS relationships for CSS rules, selectors, and properties
            for item_data, label in [(file_data['rules'], 'Rule'), (file_data['selectors'], 'Selector'), (file_data['properties'], 'Property')]:
                for item in item_data:
                    query = f"""
                        MATCH (f:File {{path: $file_path}})
                        MERGE (n:{label} {{name: $name, file_path: $file_path, line_number: $line_number}})
                        SET n += $props
                        MERGE (f)-[:CONTAINS]->(n)
                    """
                    session.run(query, file_path=file_path_str, name=item['name'], line_number=item['line_number'], props=item)

            # Create CONTAINS relationships for nested CSS rules
            for item in file_data.get('rules', []):
                if item.get("parent_rule"):
                    session.run("""
                        MATCH (outer:Rule {name: $parent_rule, file_path: $file_path})
                        MATCH (inner:Rule {name: $name, file_path: $file_path, line_number: $line_number})
                        MERGE (outer)-[:CONTAINS]->(inner)
                    """, parent_rule=item["parent_rule"], file_path=file_path_str, name=item["name"], line_number=item["line_number"])

            # Handle CSS imports and create IMPORTS relationships
            for imp in file_data.get('imports', []):
                logger.info(f"Processing CSS import: {imp}")
                session.run("""
                    MATCH (f:File {path: $file_path})
                    MERGE (m:Module {name: $name})
                    SET m.url = $url, m.media = $media
                    MERGE (f)-[:IMPORTS]->(m)
                """, file_path=file_path_str, name=imp['name'], url=imp.get('url'), media=imp.get('media'))

            # Handle CONTAINS relationship between rules and their selectors/properties
            for rule in file_data.get('rules', []):
                rule_name = rule['name']
                # Connect rule to its selectors
                for selector in file_data.get('selectors', []):
                    if selector.get('rule_name') == rule_name:
                        session.run("""
                            MATCH (r:Rule {name: $rule_name, file_path: $file_path})
                            MATCH (s:Selector {name: $selector_name, file_path: $file_path, line_number: $line_number})
                            MERGE (r)-[:HAS_SELECTOR]->(s)
                        """, rule_name=rule_name, file_path=file_path_str, selector_name=selector['name'], line_number=selector['line_number'])
                
                # Connect rule to its properties
                for prop in file_data.get('properties', []):
                    if prop.get('rule_name') == rule_name:
                        session.run("""
                            MATCH (r:Rule {name: $rule_name, file_path: $file_path})
                            MATCH (p:Property {name: $prop_name, file_path: $file_path, line_number: $line_number})
                            MERGE (r)-[:HAS_PROPERTY]->(p)
                        """, rule_name=rule_name, file_path=file_path_str, prop_name=prop['name'], line_number=prop['line_number'])

            # CSS specificity and cascade relationships are handled in a separate pass after all files are processed.

    # Second pass to create relationships that depend on all files being present like CSS cascade and specificity
    def _create_css_cascade_relationships(self, session, file_data: Dict, imports_map: dict):
        """Create CSS cascade and specificity relationships."""
        caller_file_path = str(Path(file_data['file_path']).resolve())
        
        # Create relationships for CSS cascade (rules that override each other)
        for rule in file_data.get('rules', []):
            rule_name = rule['name']
            specificity = rule.get('specificity', 0)
            
            # Find rules with same selectors but different specificity
            for other_rule in file_data.get('rules', []):
                if (other_rule['name'] != rule_name and 
                    other_rule.get('specificity', 0) > specificity and
                    other_rule.get('line_number', 0) > rule.get('line_number', 0)):
                    
                    session.run("""
                        MATCH (weaker:Rule {name: $weaker_name, file_path: $file_path})
                        MATCH (stronger:Rule {name: $stronger_name, file_path: $file_path})
                        MERGE (weaker)-[:OVERRIDDEN_BY {specificity_diff: $specificity_diff}]->(stronger)
                    """,
                    weaker_name=rule_name,
                    stronger_name=other_rule['name'],
                    file_path=caller_file_path,
                    specificity_diff=other_rule.get('specificity', 0) - specificity)

    def _create_all_css_cascade_relationships(self, all_file_data: list[Dict], imports_map: dict):
        """Create CSS cascade relationships for all rules after all files have been processed."""
        with self.driver.session() as session:
            for file_data in all_file_data:
                self._create_css_cascade_relationships(session, file_data, imports_map)

    def _create_css_media_relationships(self, session, file_data: Dict, imports_map: dict):
        """Create CSS media query relationships."""
        caller_file_path = str(Path(file_data['file_path']).resolve())
        
        # Create relationships for CSS media queries
        for rule in file_data.get('rules', []):
            if rule.get('media_query'):
                session.run("""
                    MATCH (r:Rule {name: $rule_name, file_path: $file_path})
                    MERGE (m:MediaQuery {name: $media_name, file_path: $file_path})
                    SET m.conditions = $conditions
                    MERGE (m)-[:CONTAINS]->(r)
                """,
                rule_name=rule['name'],
                file_path=caller_file_path,
                media_name=rule['media_query']['name'],
                conditions=rule['media_query'].get('conditions', []))

    def _create_all_css_media_relationships(self, all_file_data: list[Dict], imports_map: dict):
        """Create CSS media query relationships for all rules after all files have been processed."""
        with self.driver.session() as session:
            for file_data in all_file_data:
                self._create_css_media_relationships(session, file_data, imports_map)
                
    def delete_file_from_graph(self, file_path: str):
        """Deletes a file and all its contained elements and relationships."""
        file_path_str = str(Path(file_path).resolve())
        with self.driver.session() as session:
            parents_res = session.run("""
                MATCH (f:File {path: $path})<-[:CONTAINS*]-(d:Directory)
                RETURN d.path as path ORDER BY d.path DESC
            """, path=file_path_str)
            parent_paths = [record["path"] for record in parents_res]

            session.run(
                """
                MATCH (f:File {path: $path})
                OPTIONAL MATCH (f)-[:CONTAINS]->(element)
                DETACH DELETE f, element
                """,
                path=file_path_str,
            )
            logger.info(f"Deleted file and its elements from graph: {file_path_str}")

            for path in parent_paths:
                session.run("""
                    MATCH (d:Directory {path: $path})
                    WHERE NOT (d)-[:CONTAINS]->()
                    DETACH DELETE d
                """, path=path)

    def delete_repository_from_graph(self, repo_path: str):
        """Deletes a repository and all its contents from the graph."""
        repo_path_str = str(Path(repo_path).resolve())
        with self.driver.session() as session:
            session.run("""MATCH (r:Repository {path: $path})
                          OPTIONAL MATCH (r)-[:CONTAINS*]->(e)
                          DETACH DELETE r, e""", path=repo_path_str)
            logger.info(f"Deleted repository and its contents from graph: {repo_path_str}")

    def update_file_in_graph(self, file_path: Path, repo_path: Path, imports_map: dict):
        """Updates a single file's nodes in the graph."""
        file_path_str = str(file_path.resolve())
        repo_name = repo_path.name
        
        self.delete_file_from_graph(file_path_str)

        if file_path.exists():
            file_data = self.parse_file(repo_path, file_path)
            
            if "error" not in file_data:
                self.add_file_to_graph(file_data, repo_name, imports_map)
                return file_data
            else:
                logger.error(f"Skipping graph add for {file_path_str} due to parsing error: {file_data['error']}")
                return None
        else:
            return {"deleted": True, "path": file_path_str}

    def parse_file(self, repo_path: Path, file_path: Path, is_dependency: bool = False) -> Dict:
        """Parses a file with the appropriate language parser and extracts code elements."""
        parser = self.parsers.get(file_path.suffix)
        if not parser:
            logger.warning(f"No parser found for file extension {file_path.suffix}. Skipping {file_path}")
            return {"file_path": str(file_path), "error": f"No parser for {file_path.suffix}"}

        debug_log(f"[parse_file] Starting parsing for: {file_path} with {parser.language_name} parser")
        try:
            file_data = parser.parse(file_path, is_dependency)
            file_data['repo_path'] = str(repo_path)
            if debug_mode:
                debug_log(f"[parse_file] Successfully parsed: {file_path}")
            return file_data
        except Exception as e:
            logger.error(f"Error parsing {file_path} with {parser.language_name} parser: {e}")
            debug_log(f"[parse_file] Error parsing {file_path}: {e}")
            return {"file_path": str(file_path), "error": str(e)}

    def estimate_processing_time(self, path: Path) -> Optional[Tuple[int, float]]:
        """Estimate processing time and file count"""
        try:
            supported_extensions = self.parsers.keys()
            if path.is_file():
                if path.suffix in supported_extensions:
                    files = [path]
                else:
                    return 0, 0.0 # Not a supported file type
            else:
                all_files = path.rglob("*")
                files = [f for f in all_files if f.is_file() and f.suffix in supported_extensions]
            
            total_files = len(files)
            estimated_time = total_files * 0.05 # tree-sitter is faster
            return total_files, estimated_time
        except Exception as e:
            logger.error(f"Could not estimate processing time for {path}: {e}")
            return None

    async def build_graph_from_path_async(
        self, path: Path, is_dependency: bool = False, job_id: str = None
    ):
        """Builds graph from a directory or file path."""
        try:
            if job_id:
                self.job_manager.update_job(job_id, status=JobStatus.RUNNING)
            
            self.add_repository_to_graph(path, is_dependency)
            repo_name = path.name

            supported_extensions = self.parsers.keys()
            all_files = path.rglob("*") if path.is_dir() else [path]
            files = [f for f in all_files if f.is_file() and f.suffix in supported_extensions]
            if job_id:
                self.job_manager.update_job(job_id, total_files=len(files))
            
            debug_log("Starting pre-scan to build imports map...")
            imports_map = self._pre_scan_for_imports(files)
            debug_log(f"Pre-scan complete. Found {len(imports_map)} definitions.")

            all_file_data = []

            processed_count = 0
            for file in files:
                if file.is_file():
                    if job_id:
                        self.job_manager.update_job(job_id, current_file=str(file))
                    repo_path = path.resolve() if path.is_dir() else file.parent.resolve()
                    file_data = self.parse_file(repo_path, file, is_dependency)
                    if "error" not in file_data:
                        self.add_file_to_graph(file_data, repo_name, imports_map)
                        all_file_data.append(file_data)
                    processed_count += 1
                    if job_id:
                        self.job_manager.update_job(job_id, processed_files=processed_count)
                    await asyncio.sleep(0.01)

            self._create_all_css_media_relationships(all_file_data, imports_map)
            self._create_all_css_cascade_relationships(all_file_data, imports_map)
            
            if job_id:
                self.job_manager.update_job(job_id, status=JobStatus.COMPLETED, end_time=datetime.now())
        except Exception as e:
            error_message=str(e)
            logger.error(f"Failed to build graph for path {path}: {error_message}", exc_info=True)
            if job_id:
                '''checking if the repo got deleted '''
                if "no such file found" in error_message or "deleted" in error_message or "not found" in error_message:
                    status=JobStatus.CANCELLED
                    
                else:
                    status=JobStatus.FAILED

                self.job_manager.update_job(
                    job_id, status=JobStatus.FAILED, end_time=datetime.now(), errors=[str(e)]
                )