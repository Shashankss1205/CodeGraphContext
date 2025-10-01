
from tree_sitter import Language, Parser
from pathlib import Path
from typing import Dict
import asyncio
import logging

# Provide a basic logger if not already defined elsewhere
logger = logging.getLogger(__name__)

# Provide a basic debug_log if not defined elsewhere
def debug_log(msg):
    logger.debug(msg)

# Make sure you’ve built the tree-sitter library with html grammar:
# Language.build_library('build/my-languages.so', ['tree-sitter-html'])
HTML_LANGUAGE = Language("build/my-languages.so", "html")
parser = Parser()
parser.set_language(HTML_LANGUAGE)


def extract_html_nodes(node, source_code):
    """Recursively walk the syntax tree to extract HTML elements."""
    elements = []

    def walk(n):
        if n.type == "element":
            tag_name = None
            attributes = {}
            text_content = ""

            for child in n.children:
                if child.type == "start_tag":
                    # get tag name
                    for c in child.children:
                        if c.type == "tag_name":
                            tag_name = source_code[c.start_byte:c.end_byte]
                        if c.type == "attribute":
                            attr_key, attr_val = None, None
                            for g in c.children:
                                if g.type == "attribute_name":
                                    attr_key = source_code[g.start_byte:g.end_byte]
                                if g.type == "quoted_attribute_value":
                                    attr_val = source_code[g.start_byte:g.end_byte].strip('"').strip("'")
                            if attr_key:
                                attributes[attr_key] = attr_val

                elif child.type == "text":
                    text_content += source_code[child.start_byte:child.end_byte].strip()

            elements.append({
                "tag": tag_name,
                "attributes": attributes,
                "text": text_content,
                "start_byte": n.start_byte,
                "end_byte": n.end_byte
            })

        for c in n.children:
            walk(c)

    walk(node)
    return elements


class GraphBuilder:

    def update_file_in_graph(self, file_path: Path, repo_path: Path, imports_map: dict):
        """Update graph for an HTML file"""
        file_path_str = str(file_path.resolve())
        repo_name = repo_path.name

        debug_log(f"[update_file_in_graph] Updating HTML file: {file_path_str}")
        try:
            self.delete_file_from_graph(file_path_str)
        except Exception as e:
            logger.error(f"Error deleting old file data for {file_path_str}: {e}")
            return None

        if file_path.exists():
            file_data = self.parse_html_file(repo_path, file_path)
            if "error" not in file_data:
                self.add_file_to_graph(file_data, repo_name, imports_map)
                return file_data
            return None
        else:
            return {"deleted": True, "path": file_path_str}

    def parse_html_file(self, repo_path: Path, file_path: Path, is_dependency: bool = False) -> Dict:
        """Parse an HTML file with tree-sitter"""
        debug_log(f"[parse_html_file] Starting parse for: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            tree = parser.parse(bytes(source_code, "utf8"))
            root_node = tree.root_node
            elements = extract_html_nodes(root_node, source_code)

            return {
                "repo_path": str(repo_path),
                "file_path": str(file_path),
                "elements": elements,
                "is_dependency": is_dependency,
            }
        except Exception as e:
            logger.error(f"Error parsing HTML {file_path}: {e}")
            return {"file_path": str(file_path), "error": str(e)}

    async def build_graph_from_path_async(
        self, path: Path, is_dependency: bool = False, job_id: str = None
    ):
        """Build graph for HTML repo"""
        try:
            self.add_repository_to_graph(path, is_dependency)
            repo_name = path.name

            files = list(path.rglob("*.html")) if path.is_dir() else [path]

            imports_map = {}  # HTML has no imports, keep empty
            processed_count = 0

            for file in files:
                if file.is_file():
                    repo_path = path.resolve() if path.is_dir() else file.parent.resolve()
                    file_data = self.parse_html_file(repo_path, file, is_dependency)
                    if "error" not in file_data:
                        self.add_file_to_graph(file_data, repo_name, imports_map)
                    processed_count += 1
                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Failed to build graph for HTML path {path}: {e}", exc_info=True)
