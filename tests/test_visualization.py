# tests/test_visualization.py
"""
Tests for the visualization module and --visual flag functionality.

These tests verify that:
- The visualizer module generates correct HTML
- The --visual flag works at both global and command levels
- Different visualization types produce appropriate output
- Edge cases are handled gracefully
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

# Import the visualizer module
from codegraphcontext.cli.visualizer import (
    get_visualization_dir,
    generate_filename,
    get_node_color,
    generate_html_template,
    visualize_call_graph,
    visualize_call_chain,
    visualize_dependencies,
    visualize_inheritance_tree,
    visualize_overrides,
    visualize_search_results,
    visualize_cypher_results,
    check_visual_flag,
    escape_html,
    _safe_json_dumps,
)

# Import the CLI app for integration tests
from codegraphcontext.cli.main import app


runner = CliRunner()


class TestVisualizerUtilities:
    """Tests for utility functions in the visualizer module."""
    
    def test_get_visualization_dir_creates_directory(self):
        """Test that get_visualization_dir creates the directory if it doesn't exist."""
        viz_dir = get_visualization_dir()
        assert viz_dir.exists()
        assert viz_dir.is_dir()
        assert viz_dir == Path.home() / ".codegraphcontext" / "visualizations"
    
    def test_generate_filename_format(self):
        """Test that generate_filename produces correctly formatted filenames."""
        filename = generate_filename("test_prefix")
        assert filename.startswith("test_prefix_")
        assert filename.endswith(".html")
        # Should have timestamp format: prefix_YYYYMMDD_HHMMSS.html
        parts = filename.replace(".html", "").split("_")
        assert len(parts) >= 3
    
    def test_get_node_color_known_types(self):
        """Test that get_node_color returns correct colors for known types."""
        function_color = get_node_color("Function")
        assert "background" in function_color
        assert "border" in function_color
        assert function_color["background"] == "#4caf50"  # Green
        
        class_color = get_node_color("Class")
        assert class_color["background"] == "#ff9800"  # Orange
    
    def test_get_node_color_unknown_type(self):
        """Test that get_node_color returns default color for unknown types."""
        unknown_color = get_node_color("UnknownType")
        assert "background" in unknown_color
        assert unknown_color["background"] == "#97c2fc"  # Default blue
    
    def test_escape_html_basic(self):
        """Test escape_html escapes special characters."""
        assert escape_html("<script>") == "&lt;script&gt;"
        assert escape_html("a & b") == "a &amp; b"
        assert escape_html('"quotes"') == "&quot;quotes&quot;"
    
    def test_escape_html_none(self):
        """Test escape_html handles None."""
        assert escape_html(None) == ""
    
    def test_escape_html_non_string(self):
        """Test escape_html handles non-string types."""
        assert escape_html(123) == "123"
    
    def test_safe_json_dumps_basic(self):
        """Test _safe_json_dumps handles normal dicts."""
        result = _safe_json_dumps({"name": "test", "value": 123})
        assert "test" in result
        assert "123" in result
    
    def test_safe_json_dumps_non_serializable(self):
        """Test _safe_json_dumps handles non-serializable objects gracefully."""
        class NonSerializable:
            def __str__(self):
                return "custom_object"
        
        # Should not raise, should convert to string
        result = _safe_json_dumps({"obj": NonSerializable()})
        assert "custom_object" in result


class TestHtmlTemplateGeneration:
    """Tests for HTML template generation."""
    
    def test_generate_html_template_basic(self):
        """Test basic HTML template generation."""
        nodes = [
            {"id": "1", "label": "func1", "group": "Function", "color": {"background": "#4caf50"}},
            {"id": "2", "label": "func2", "group": "Function", "color": {"background": "#4caf50"}},
        ]
        edges = [
            {"from": "1", "to": "2", "label": "calls", "arrows": "to"},
        ]
        
        html = generate_html_template(nodes, edges, "Test Graph")
        
        # Check essential elements
        assert "<!DOCTYPE html>" in html
        assert "<title>Test Graph - CodeGraphContext</title>" in html
        assert "vis-network" in html
        assert "func1" in html
        assert "func2" in html
        assert "Nodes:" in html
        assert "Edges:" in html
    
    def test_generate_html_template_hierarchical_layout(self):
        """Test HTML template with hierarchical layout."""
        nodes = [{"id": "1", "label": "node1", "group": "Node"}]
        edges = []
        
        html = generate_html_template(nodes, edges, "Hierarchical Test", layout_type="hierarchical")
        
        assert "hierarchical" in html
        assert "direction: 'UD'" in html  # Up-Down direction
    
    def test_generate_html_template_force_layout(self):
        """Test HTML template with force-directed layout."""
        nodes = [{"id": "1", "label": "node1", "group": "Node"}]
        edges = []
        
        html = generate_html_template(nodes, edges, "Force Test", layout_type="force")
        
        assert "forceAtlas2Based" in html
    
    def test_generate_html_template_empty_nodes(self):
        """Test HTML template with empty nodes list."""
        html = generate_html_template([], [], "Empty Graph")
        
        assert "<!DOCTYPE html>" in html
        # Check for node count - format may vary but should show 0
        assert "nodesData" in html  # Nodes data should be present (even if empty)


class TestVisualizationFunctions:
    """Tests for specific visualization functions."""
    
    @patch('codegraphcontext.cli.visualizer.save_and_open_visualization')
    def test_visualize_call_graph_outgoing(self, mock_save):
        """Test visualize_call_graph for outgoing calls."""
        mock_save.return_value = "/tmp/test.html"
        
        results = [
            {"called_function": "helper1", "called_file_path": "/src/helper.py", "called_line_number": 10},
            {"called_function": "helper2", "called_file_path": "/src/helper.py", "called_line_number": 20},
        ]
        
        path = visualize_call_graph(results, "main_func", direction="outgoing")
        
        assert path == "/tmp/test.html"
        mock_save.assert_called_once()
        # Check that the HTML contains the function name
        call_args = mock_save.call_args
        html_content = call_args[0][0]
        assert "main_func" in html_content
        assert "helper1" in html_content
    
    @patch('codegraphcontext.cli.visualizer.save_and_open_visualization')
    def test_visualize_call_graph_incoming(self, mock_save):
        """Test visualize_call_graph for incoming callers."""
        mock_save.return_value = "/tmp/test.html"
        
        results = [
            {"caller_function": "caller1", "caller_file_path": "/src/main.py", "caller_line_number": 5},
        ]
        
        path = visualize_call_graph(results, "target_func", direction="incoming")
        
        assert path == "/tmp/test.html"
        mock_save.assert_called_once()
    
    def test_visualize_call_graph_empty_results(self):
        """Test visualize_call_graph with empty results."""
        path = visualize_call_graph([], "func", direction="outgoing")
        assert path is None
    
    @patch('codegraphcontext.cli.visualizer.save_and_open_visualization')
    def test_visualize_call_chain(self, mock_save):
        """Test visualize_call_chain."""
        mock_save.return_value = "/tmp/test.html"
        
        results = [
            {
                "chain_length": 3,
                "function_chain": [
                    {"name": "main", "file_path": "/main.py", "line_number": 1},
                    {"name": "process", "file_path": "/process.py", "line_number": 10},
                    {"name": "helper", "file_path": "/helper.py", "line_number": 20},
                ]
            }
        ]
        
        path = visualize_call_chain(results, "main", "helper")
        
        assert path == "/tmp/test.html"
        mock_save.assert_called_once()
    
    def test_visualize_call_chain_empty_results(self):
        """Test visualize_call_chain with empty results."""
        path = visualize_call_chain([], "start", "end")
        assert path is None
    
    @patch('codegraphcontext.cli.visualizer.save_and_open_visualization')
    def test_visualize_dependencies(self, mock_save):
        """Test visualize_dependencies."""
        mock_save.return_value = "/tmp/test.html"
        
        results = {
            "importers": [
                {"importer_file_path": "/src/app.py", "import_line_number": 5},
            ],
            "imports": [
                {"imported_module": "requests", "import_alias": ""},
            ]
        }
        
        path = visualize_dependencies(results, "mymodule")
        
        assert path == "/tmp/test.html"
        mock_save.assert_called_once()
    
    def test_visualize_dependencies_empty_results(self):
        """Test visualize_dependencies with empty results."""
        path = visualize_dependencies({"importers": [], "imports": []}, "module")
        assert path is None
    
    @patch('codegraphcontext.cli.visualizer.save_and_open_visualization')
    def test_visualize_inheritance_tree(self, mock_save):
        """Test visualize_inheritance_tree."""
        mock_save.return_value = "/tmp/test.html"
        
        results = {
            "parent_classes": [
                {"parent_class": "BaseClass", "parent_file_path": "/base.py"},
            ],
            "child_classes": [
                {"child_class": "ChildClass", "child_file_path": "/child.py"},
            ],
            "methods": [
                {"method_name": "do_something", "method_args": "self"},
            ]
        }
        
        path = visualize_inheritance_tree(results, "MyClass")
        
        assert path == "/tmp/test.html"
        mock_save.assert_called_once()
    
    def test_visualize_inheritance_tree_empty_results(self):
        """Test visualize_inheritance_tree with no hierarchy."""
        path = visualize_inheritance_tree({"parent_classes": [], "child_classes": []}, "Orphan")
        assert path is None
    
    @patch('codegraphcontext.cli.visualizer.save_and_open_visualization')
    def test_visualize_overrides(self, mock_save):
        """Test visualize_overrides."""
        mock_save.return_value = "/tmp/test.html"
        
        results = [
            {"class_name": "Circle", "function_name": "area", "class_file_path": "/shapes.py", "function_line_number": 10},
            {"class_name": "Square", "function_name": "area", "class_file_path": "/shapes.py", "function_line_number": 25},
        ]
        
        path = visualize_overrides(results, "area")
        
        assert path == "/tmp/test.html"
        mock_save.assert_called_once()
    
    def test_visualize_overrides_empty_results(self):
        """Test visualize_overrides with empty results."""
        path = visualize_overrides([], "method")
        assert path is None
    
    @patch('codegraphcontext.cli.visualizer.save_and_open_visualization')
    def test_visualize_search_results(self, mock_save):
        """Test visualize_search_results."""
        mock_save.return_value = "/tmp/test.html"
        
        results = [
            {"name": "UserController", "type": "Class", "file_path": "/controllers.py", "line_number": 10},
            {"name": "user_helper", "type": "Function", "file_path": "/helpers.py", "line_number": 5},
        ]
        
        path = visualize_search_results(results, "user", search_type="pattern")
        
        assert path == "/tmp/test.html"
        mock_save.assert_called_once()
    
    def test_visualize_search_results_empty(self):
        """Test visualize_search_results with empty results."""
        path = visualize_search_results([], "nothing", search_type="name")
        assert path is None
    
    @patch('codegraphcontext.cli.visualizer.save_and_open_visualization')
    def test_visualize_cypher_results(self, mock_save):
        """Test visualize_cypher_results."""
        mock_save.return_value = "/tmp/test.html"
        
        records = [
            {"n": {"id": 1, "name": "func1", "labels": ["Function"]}},
            {"n": {"id": 2, "name": "func2", "labels": ["Function"]}},
        ]
        
        path = visualize_cypher_results(records, "MATCH (n) RETURN n")
        
        assert path == "/tmp/test.html"
        mock_save.assert_called_once()
    
    def test_visualize_cypher_results_empty(self):
        """Test visualize_cypher_results with empty results."""
        path = visualize_cypher_results([], "MATCH (n) RETURN n")
        assert path is None


class TestCheckVisualFlag:
    """Tests for the check_visual_flag utility function."""
    
    def test_check_visual_flag_local_true(self):
        """Test check_visual_flag when local flag is True."""
        ctx = MagicMock()
        ctx.obj = {}
        
        result = check_visual_flag(ctx, local_visual=True)
        assert result is True
    
    def test_check_visual_flag_global_true(self):
        """Test check_visual_flag when global flag is True."""
        ctx = MagicMock()
        ctx.obj = {"visual": True}
        
        result = check_visual_flag(ctx, local_visual=False)
        assert result is True
    
    def test_check_visual_flag_both_true(self):
        """Test check_visual_flag when both flags are True."""
        ctx = MagicMock()
        ctx.obj = {"visual": True}
        
        result = check_visual_flag(ctx, local_visual=True)
        assert result is True
    
    def test_check_visual_flag_both_false(self):
        """Test check_visual_flag when both flags are False."""
        ctx = MagicMock()
        ctx.obj = {"visual": False}
        
        result = check_visual_flag(ctx, local_visual=False)
        assert result is False
    
    def test_check_visual_flag_no_context(self):
        """Test check_visual_flag with None context."""
        result = check_visual_flag(None, local_visual=False)
        assert result is False
        
        result = check_visual_flag(None, local_visual=True)
        assert result is True
    
    def test_check_visual_flag_empty_context_obj(self):
        """Test check_visual_flag with empty context object."""
        ctx = MagicMock()
        ctx.obj = None
        
        result = check_visual_flag(ctx, local_visual=False)
        assert result is False


class TestCLIVisualFlagIntegration:
    """Integration tests for the --visual flag in CLI commands."""
    
    def test_global_visual_flag_help(self):
        """Test that global --visual flag appears in help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_analyze_calls_visual_flag_help(self):
        """Test that --visual flag appears in analyze calls help."""
        result = runner.invoke(app, ["analyze", "calls", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_analyze_callers_visual_flag_help(self):
        """Test that --visual flag appears in analyze callers help."""
        result = runner.invoke(app, ["analyze", "callers", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_analyze_chain_visual_flag_help(self):
        """Test that --visual flag appears in analyze chain help."""
        result = runner.invoke(app, ["analyze", "chain", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_analyze_deps_visual_flag_help(self):
        """Test that --visual flag appears in analyze deps help."""
        result = runner.invoke(app, ["analyze", "deps", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_analyze_tree_visual_flag_help(self):
        """Test that --visual flag appears in analyze tree help."""
        result = runner.invoke(app, ["analyze", "tree", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_analyze_overrides_visual_flag_help(self):
        """Test that --visual flag appears in analyze overrides help."""
        result = runner.invoke(app, ["analyze", "overrides", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_find_name_visual_flag_help(self):
        """Test that --visual flag appears in find name help."""
        result = runner.invoke(app, ["find", "name", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_find_pattern_visual_flag_help(self):
        """Test that --visual flag appears in find pattern help."""
        result = runner.invoke(app, ["find", "pattern", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_find_type_visual_flag_help(self):
        """Test that --visual flag appears in find type help."""
        result = runner.invoke(app, ["find", "type", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_query_visual_flag_help(self):
        """Test that --visual flag appears in query help."""
        result = runner.invoke(app, ["query", "--help"])
        assert result.exit_code == 0
        assert "--visual" in result.output or "-V" in result.output
    
    def test_version_flag_not_affected(self):
        """Test that -v still works for version."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        # Should show version, not trigger visualization
        assert "CodeGraphContext" in result.output


class TestHtmlOutputValidation:
    """Tests to validate HTML output structure."""
    
    def test_html_is_standalone(self):
        """Test that generated HTML is standalone and doesn't require external files."""
        nodes = [{"id": "1", "label": "test", "group": "Test"}]
        edges = []
        
        html = generate_html_template(nodes, edges, "Standalone Test")
        
        # Check for CDN links (these are allowed for standalone)
        assert "https://unpkg.com/vis-network" in html
        
        # Check that all styles are inline
        assert "<style" in html
        assert "</style>" in html
        
        # Check that all scripts are inline or CDN
        assert "<script" in html
        assert "</script>" in html
    
    def test_html_has_proper_encoding(self):
        """Test that HTML has proper encoding meta tag."""
        nodes = [{"id": "1", "label": "test", "group": "Test"}]
        edges = []
        
        html = generate_html_template(nodes, edges, "Encoding Test")
        
        assert 'charset="utf-8"' in html or "charset='utf-8'" in html
    
    def test_html_handles_special_characters(self):
        """Test that HTML handles special characters in node labels."""
        nodes = [
            {"id": "1", "label": 'func<T>', "group": "Function"},
            {"id": "2", "label": "process & handle", "group": "Function"},
            {"id": "3", "label": '"quoted"', "group": "Function"},
        ]
        edges = []
        
        html = generate_html_template(nodes, edges, "Special Chars Test")
        
        # Should not raise an error and should produce valid HTML
        assert "<!DOCTYPE html>" in html
        # JSON encoding should handle special chars
        assert "nodesData" in html
    def test_html_xss_protection_in_title(self):
        """Test that title is properly escaped to prevent XSS attacks."""
        nodes = [{"id": "1", "label": "test", "group": "Test"}]
        edges = []
        
        # Attempt XSS via title
        malicious_title = '<script>alert("XSS")</script>'
        html = generate_html_template(nodes, edges, malicious_title)
        
        # The script tag should be escaped, not raw
        assert '<script>alert("XSS")</script>' not in html
        assert '&lt;script&gt;' in html or 'script&gt;' in html
    
    def test_html_xss_protection_in_description(self):
        """Test that description is properly escaped to prevent XSS attacks."""
        nodes = [{"id": "1", "label": "test", "group": "Test"}]
        edges = []
        
        # Attempt XSS via description
        malicious_desc = '<img src=x onerror=alert(1)>'
        html = generate_html_template(nodes, edges, "Safe Title", description=malicious_desc)
        
        # The malicious tag should be escaped
        assert '<img src=x onerror=alert(1)>' not in html
        assert '&lt;img' in html or 'src=x' not in html