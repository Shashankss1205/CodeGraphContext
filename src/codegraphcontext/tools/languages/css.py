from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

CSS_QUERIES = {
    "rules": """
        (rule_set) @rule_set
    """,
    "selectors": """
        (class_selector) @class_selector
        (id_selector) @id_selector
        (tag_name) @tag_name
        (universal_selector) @universal_selector
        (descendant_selector) @descendant_selector
    """,
    "declarations": """
        (declaration) @declaration
    """,
    "at_rules": """
        (import_statement) @import_statement
        (media_statement) @media_statement
    """,
    "imports": """
        (import_statement) @import_statement
    """,
    "media_queries": """
        (media_statement) @media_statement
    """,
}

class CSSTreeSitterParser:
    """A CSS-specific parser using tree-sitter, encapsulating language-specific logic."""

    def __init__(self, generic_parser_wrapper):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = generic_parser_wrapper.language_name
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

        self.queries = {
            name: self.language.query(query_str)
            for name, query_str in CSS_QUERIES.items()
        }

    def _get_node_text(self, node) -> str:
        return node.text.decode('utf-8')

    def _get_parent_context(self, node, types=('rule_set', 'at_rule')):
        curr = node.parent
        while curr:
            if curr.type in types:
                if curr.type == 'rule_set':
                    # Get the first selector as the rule name
                    selectors = [child for child in curr.children if child.type == 'selector']
                    if selectors:
                        return self._get_node_text(selectors[0]), curr.type, curr.start_point[0] + 1
                elif curr.type == 'at_rule':
                    # Get the at-rule name
                    name_node = curr.child_by_field_name('name')
                    if name_node:
                        return self._get_node_text(name_node), curr.type, curr.start_point[0] + 1
            curr = curr.parent
        return None, None, None

    def _calculate_specificity(self, selector_text: str) -> int:
        """Calculate CSS specificity for a selector."""
        # Simple specificity calculation: count IDs, classes, and elements
        id_count = selector_text.count('#')
        class_count = selector_text.count('.')
        element_count = len([part for part in selector_text.split() if part and not part.startswith(('.', '#', ':', '['))])
        
        # Weight: IDs (100), classes (10), elements (1)
        return id_count * 100 + class_count * 10 + element_count

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict:
        """Parses a CSS file and returns its structure in a standardized dictionary format."""
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        rules = self._find_rules(root_node)
        selectors = self._find_selectors(root_node)
        properties = self._find_properties(root_node)
        imports = self._find_imports(root_node)
        media_queries = self._find_media_queries(root_node)

        return {
            "file_path": str(file_path),
            "rules": rules,
            "selectors": selectors,
            "properties": properties,
            "imports": imports,
            "media_queries": media_queries,
            "is_dependency": is_dependency,
            "lang": self.language_name,
        }

    def _find_rules(self, root_node):
        rules = []
        query = self.queries['rules']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name == 'rule_set':
                # Get selectors for this rule
                selectors_node = None
                for child in node.children:
                    if child.type == 'selectors':
                        selectors_node = child
                        break
                if not selectors_node:
                    continue
                
                # Get all selector types
                selectors = []
                for child in selectors_node.children:
                    if child.type in ['class_selector', 'id_selector', 'tag_name', 'universal_selector', 'descendant_selector']:
                        selectors.append(self._get_node_text(child))
                
                if not selectors:
                    continue
                
                # Use the first selector as the rule name
                rule_name = selectors[0]
                
                # Get the block (declarations)
                block_node = None
                for child in node.children:
                    if child.type == 'block':
                        block_node = child
                        break
                declarations = []
                if block_node:
                    declarations = [child for child in block_node.children if child.type == 'declaration']

                context, context_type, _ = self._get_parent_context(node)

                rule_data = {
                    "name": rule_name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "selectors": selectors,
                    "declaration_count": len(declarations),
                    "source": self._get_node_text(node),
                    "specificity": self._calculate_specificity(rule_name),
                    "context": context,
                    "context_type": context_type,
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                rules.append(rule_data)
        return rules

    def _find_selectors(self, root_node):
        selectors = []
        query = self.queries['selectors']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name in ['class_selector', 'id_selector', 'tag_name', 'universal_selector', 'descendant_selector']:
                selector_text = self._get_node_text(node)
                rule_node = node.parent
                
                # Find the rule this selector belongs to
                while rule_node and rule_node.type != 'rule_set':
                    rule_node = rule_node.parent
                
                rule_name = None
                if rule_node:
                    selectors_node = None
                    for child in rule_node.children:
                        if child.type == 'selectors':
                            selectors_node = child
                            break
                    if selectors_node:
                        first_selector = None
                        for child in selectors_node.children:
                            if child.type in ['class_selector', 'id_selector', 'tag_name', 'universal_selector', 'descendant_selector']:
                                first_selector = child
                                break
                        if first_selector:
                            rule_name = self._get_node_text(first_selector)

                context, context_type, _ = self._get_parent_context(node)

                selector_data = {
                    "name": selector_text,
                    "line_number": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "specificity": self._calculate_specificity(selector_text),
                    "rule_name": rule_name,
                    "source": self._get_node_text(node),
                    "context": context,
                    "context_type": context_type,
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                selectors.append(selector_data)
        return selectors

    def _find_properties(self, root_node):
        properties = []
        query = self.queries['declarations']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name == 'declaration':
                # Get property name
                property_node = None
                for child in node.children:
                    if child.type == 'property_name':
                        property_node = child
                        break
                if not property_node:
                    continue
                
                property_name = self._get_node_text(property_node)
                
                # Get property value
                value_node = None
                for child in node.children:
                    if child.type in ['plain_value', 'integer_value', 'color_value']:
                        value_node = child
                        break
                property_value = self._get_node_text(value_node) if value_node else None
                
                # Find the rule this property belongs to
                rule_node = node.parent
                while rule_node and rule_node.type != 'rule_set':
                    rule_node = rule_node.parent
                
                rule_name = None
                if rule_node:
                    selectors_node = None
                    for child in rule_node.children:
                        if child.type == 'selectors':
                            selectors_node = child
                            break
                    if selectors_node:
                        first_selector = None
                        for child in selectors_node.children:
                            if child.type in ['class_selector', 'id_selector', 'tag_name', 'universal_selector', 'descendant_selector']:
                                first_selector = child
                                break
                        if first_selector:
                            rule_name = self._get_node_text(first_selector)

                context, context_type, _ = self._get_parent_context(node)

                property_data = {
                    "name": property_name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "value": property_value,
                    "rule_name": rule_name,
                    "source": self._get_node_text(node),
                    "context": context,
                    "context_type": context_type,
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                properties.append(property_data)
        return properties

    def _find_imports(self, root_node):
        imports = []
        query = self.queries['imports']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name == 'import_statement':
                # Extract URL from import statement
                import_text = self._get_node_text(node)
                
                # Look for call_expression with url()
                call_expr = None
                for child in node.children:
                    if child.type == 'call_expression':
                        call_expr = child
                        break
                
                url = None
                if call_expr:
                    # Get the string value from the call expression
                    for child in call_expr.children:
                        if child.type == 'string_value':
                            url = self._get_node_text(child).strip('"\'')
                            break
                
                # Extract media queries if present
                media = None
                if 'media' in import_text.lower():
                    # Simple media extraction
                    media_start = import_text.lower().find('media')
                    if media_start != -1:
                        media = import_text[media_start:].strip()

                import_data = {
                    "name": url or "unknown",
                    "url": url,
                    "media": media,
                    "line_number": node.start_point[0] + 1,
                    "source": self._get_node_text(node),
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                imports.append(import_data)
        return imports

    def _find_media_queries(self, root_node):
        media_queries = []
        query = self.queries['media_queries']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name == 'media_statement':
                # Extract feature query conditions
                feature_query = None
                for child in node.children:
                    if child.type == 'feature_query':
                        feature_query = child
                        break
                
                conditions = []
                if feature_query:
                    # Extract feature name and value
                    feature_name = None
                    feature_value = None
                    for child in feature_query.children:
                        if child.type == 'feature_name':
                            feature_name = self._get_node_text(child)
                        elif child.type == 'integer_value':
                            feature_value = self._get_node_text(child)
                    
                    if feature_name and feature_value:
                        conditions.append(f"{feature_name}: {feature_value}")
                
                media_data = {
                    "name": f"media_{node.start_point[0] + 1}",
                    "conditions": conditions,
                    "line_number": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "source": self._get_node_text(node),
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                media_queries.append(media_data)
        return media_queries

def pre_scan_css(files: list[Path], parser_wrapper) -> dict:
    """Scans CSS files to create a map of rule names to their file paths."""
    imports_map = {}
    query_str = """
        (rule_set
            selectors: (selectors) @selectors)
    """
    query = parser_wrapper.language.query(query_str)
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = parser_wrapper.parser.parse(bytes(f.read(), "utf8"))
            
            for capture, _ in query.captures(tree.root_node):
                # Get the first selector from the selectors node
                selectors_node = capture
                first_selector = None
                for child in selectors_node.children:
                    if child.type in ['class_selector', 'id_selector', 'tag_name', 'universal_selector', 'descendant_selector']:
                        first_selector = child
                        break
                
                if first_selector:
                    name = first_selector.text.decode('utf-8')
                    if name not in imports_map:
                        imports_map[name] = []
                    imports_map[name].append(str(file_path.resolve()))
        except Exception as e:
            logger.warning(f"Tree-sitter pre-scan failed for {file_path}: {e}")
    return imports_map
