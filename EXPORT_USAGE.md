# Graph Export Functionality

CodeGraphContext now supports exporting code graph visualizations in multiple formats through both the MCP server and CLI interface.

## Installation

To use the export functionality, install the visualization dependencies:

```bash
pip install 'codegraphcontext[visualization]'
```

This installs the required dependencies:
- matplotlib>=3.5.0 (for PNG, SVG, PDF exports)
- networkx>=2.8.0 (for graph layout algorithms)
- plotly>=5.15.0 (for interactive HTML exports)

## CLI Usage

### Basic Export
```bash
cgc export output.png
```

### Export Options
```bash
cgc export graph.svg \
  --format svg \
  --layout spring \
  --max-nodes 500 \
  --width 1600 \
  --height 1200 \
  --dpi 300
```

### Available Formats
- **PNG**: Static raster image (default)
- **SVG**: Vector graphics format
- **PDF**: Portable document format
- **HTML**: Interactive visualization with Plotly
- **JSON**: Graph data in JSON format
- **GraphML**: Standard graph markup language

### Layout Algorithms
- **spring**: Force-directed layout (default)
- **circular**: Nodes arranged in a circle
- **kamada_kawai**: Kamada-Kawai force-directed algorithm
- **planar**: Planar layout for planar graphs
- **random**: Random node positions
- **shell**: Concentric circles layout
- **spectral**: Spectral layout using graph Laplacian

### Filter Options
```bash
# Export only specific repository
cgc export repo_graph.png --repository "/path/to/repo"

# Exclude dependency nodes
cgc export clean_graph.png --exclude-deps

# Limit graph size
cgc export small_graph.png --max-nodes 100

# Hide node labels
cgc export unlabeled.png --no-labels
```

## MCP Server Usage

The export functionality is available as an MCP tool when running the server:

```json
{
  "name": "export_graph_visualization",
  "arguments": {
    "output_path": "graph.png",
    "format": "png",
    "layout": "spring",
    "max_nodes": 1000,
    "width": 1200,
    "height": 800,
    "show_labels": true,
    "dpi": 300
  }
}
```

## Examples

### Create a high-quality PDF report
```bash
cgc export project_structure.pdf \
  --format pdf \
  --layout kamada_kawai \
  --width 2400 \
  --height 1600 \
  --dpi 600 \
  --max-nodes 200
```

### Generate interactive HTML visualization
```bash
cgc export interactive_graph.html \
  --format html \
  --layout spring \
  --include-deps
```

### Export graph data for analysis
```bash
cgc export graph_data.json --format json
cgc export graph_structure.graphml --format graphml
```

### Repository-specific visualization
```bash
cgc export frontend_graph.svg \
  --repository "src/frontend" \
  --format svg \
  --layout circular \
  --exclude-deps
```

## Output Information

The export command provides detailed information about the generated visualization:
- Number of nodes and edges
- File size
- Output path
- Export format used

## Error Handling

If visualization dependencies are not installed, the command will provide clear instructions:

```
Error: Matplotlib and NetworkX are required for static image exports.
Install with: pip install 'codegraphcontext[visualization]'
```

## Integration with Existing Workflow

The export functionality integrates seamlessly with the existing CodeGraphContext workflow:

1. **Index your code**: `cgc setup` and `cgc start`
2. **Generate visualization**: `cgc export my_graph.png`
3. **Use in documentation**: Include the exported images in README files, documentation, or presentations

This makes it easy to create visual documentation of your codebase structure and share insights about code relationships and dependencies.

## Advanced Usage

### Custom Styling for Different Node Types

The export system automatically colors nodes based on their types and relationships:
- Functions are colored based on their complexity
- Classes are grouped by inheritance
- Dependencies are visually distinguished
- File relationships are clearly shown

### Performance Considerations

For large codebases:
- Use `--max-nodes` to limit the visualization size
- Consider `--exclude-deps` to focus on your code
- Use `--repository` to export specific parts of the codebase
- PNG format is fastest for large graphs
- HTML format provides the best interactivity

### Batch Export

You can create multiple visualizations programmatically:

```bash
# Overview of entire codebase
cgc export overview.png --max-nodes 100 --exclude-deps

# Detailed view of core modules
cgc export core_detailed.svg --repository "src/core" --format svg

# Interactive exploration
cgc export interactive.html --format html --include-deps
```

This export functionality provides a comprehensive solution for visualizing and sharing code structure insights.