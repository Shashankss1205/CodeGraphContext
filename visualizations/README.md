# 📊 CodeGraphContext Visualization Suite

Transform your code graph into beautiful, actionable diagrams!

## 🎯 Overview

This visualization suite provides **three powerful options** to convert your CodeGraphContext graph database into useful diagrams:

### **Option A: Enhanced Interactive Multi-Mode Visualizer** 🎨
An interactive HTML visualization with dynamic filtering and multiple diagram modes.

**Features:**
- 🔄 **Multiple Diagram Modes**: Switch between call graphs, imports, inheritance, and structure views
- 🎛️ **Dynamic Filtering**: Toggle node types (Functions, Classes, Modules, Files)
- 🎯 **Multiple Layouts**: Force Atlas, Hierarchical, Barnes Hut, Repulsion
- 💫 **Interactive**: Drag, zoom, click for details
- 🎨 **Beautiful UI**: Modern dark theme with smooth animations

**Use Cases:**
- Exploring code relationships interactively
- Understanding call flows and dependencies
- Presenting code architecture to teams
- Debugging complex codebases

---

### **Option B: Static Diagram Generators** 📦
Export your graph to industry-standard diagram formats for documentation.

**Formats:**
- **PlantUML** (`.puml`): UML class diagrams
- **Mermaid** (`.mmd`): Flowcharts and class diagrams
- **Graphviz DOT** (`.dot`): Call graphs, imports, inheritance

**Features:**
- 📄 **Documentation-Ready**: Perfect for README files, wikis, and docs
- 🔧 **Tool Integration**: Works with PlantUML, Mermaid Live, Graphviz
- 🎨 **Multiple Perspectives**: Separate diagrams for calls, imports, inheritance
- 📤 **Easy Sharing**: Text-based formats for version control

**Use Cases:**
- Adding diagrams to documentation
- Code reviews and design discussions
- Architecture documentation
- Integration with existing tools

---

### **Option C: Architectural Analyzer** 🏗️
High-level architectural view with module grouping and dependency analysis.

**Features:**
- 📦 **Module Grouping**: Automatically groups code into logical modules
- 🔗 **Dependency Analysis**: Visualizes inter-module dependencies
- 📊 **Complexity Metrics**: Shows module size and complexity
- 📝 **Architecture Report**: Detailed Markdown report with insights
- 🎯 **Hierarchical Layout**: Clear, organized view of system architecture

**Use Cases:**
- Understanding system architecture at a glance
- Identifying tightly coupled modules
- Planning refactoring efforts
- Onboarding new team members

---

## 🚀 Quick Start

### Prerequisites
Make sure you have indexed your codebase:
```bash
cgc index /path/to/your/project
```

### Run All Visualizations
```bash
cd visualizations
python generate_all.py
```

This will generate **all** visualization outputs in one go!

### Run Individual Options

**Option A - Interactive Visualizer:**
```bash
python option_a_interactive.py
# Opens: option_a_interactive.html
```

**Option B - Static Exports:**
```bash
python option_b_export.py
# Generates: PlantUML, Mermaid, and Graphviz files
```

**Option C - Architecture:**
```bash
python option_c_architecture.py
# Generates: Interactive HTML + Markdown report
```

---

## 📁 Output Files

### Option A
- `option_a_interactive.html` - Interactive multi-mode visualizer

### Option B
- `option_b_plantuml_class.puml` - PlantUML class diagram
- `option_b_mermaid_class.mmd` - Mermaid class diagram
- `option_b_mermaid_calls.mmd` - Mermaid call flowchart
- `option_b_graphviz_calls.dot` - Graphviz call graph
- `option_b_graphviz_imports.dot` - Graphviz import graph
- `option_b_graphviz_inherits.dot` - Graphviz inheritance graph

### Option C
- `option_c_architecture.html` - Interactive architecture diagram
- `option_c_report.md` - Detailed architecture report

---

## 🎨 Viewing Your Diagrams

### Interactive HTML Files (Options A & C)
Simply open the HTML files in your browser:
```bash
# Linux/Mac
xdg-open option_a_interactive.html

# Mac
open option_a_interactive.html

# Windows
start option_a_interactive.html
```

### PlantUML Files
1. **Online**: Visit [PlantUML Online](https://www.plantuml.com/plantuml/uml/)
2. **Local**: Install PlantUML and run:
   ```bash
   plantuml option_b_plantuml_class.puml
   ```

### Mermaid Files
1. **Online**: Visit [Mermaid Live Editor](https://mermaid.live/)
2. **In Markdown**: Many platforms (GitHub, GitLab, Notion) render Mermaid directly

### Graphviz DOT Files
1. **Online**: Visit [Graphviz Online](https://dreampuf.github.io/GraphvizOnline/)
2. **Local**: Install Graphviz and run:
   ```bash
   dot -Tpng option_b_graphviz_calls.dot -o calls.png
   dot -Tsvg option_b_graphviz_imports.dot -o imports.svg
   ```

---

## 💡 Use Case Examples

### 1. **Understanding a New Codebase**
Run **Option A** to interactively explore:
- Start with "All" mode to see the big picture
- Switch to "Call Graph" to understand execution flow
- Filter to show only Classes to see OOP structure

### 2. **Documentation**
Run **Option B** to generate diagrams for your README:
```markdown
## Architecture

```mermaid
[paste content from option_b_mermaid_class.mmd]
```
```

### 3. **Refactoring Planning**
Run **Option C** to identify:
- Tightly coupled modules (many dependencies)
- Large, complex modules (high function/class count)
- Architectural violations (unexpected dependencies)

### 4. **Code Review**
Run **Option B** to generate call graphs:
- Show what functions a new feature calls
- Identify potential side effects
- Verify architectural boundaries

---

## 🎯 Customization

### Filtering Specific Functions/Classes
Edit the query in the respective Python file to focus on specific code:

```python
# In option_a_interactive.py or option_b_export.py
query = """
    MATCH (f:Function)-[:CALLS]->(called:Function)
    WHERE f.file_path CONTAINS 'my_module'
    RETURN f.name, called.name
"""
```

### Changing Colors/Styles
Edit the HTML/CSS in the generated files or modify the Python scripts:

```python
# In option_a_interactive.py
groupColors = {
    'Function': { 'background': '#your_color', 'border': '#border_color' }
}
```

---

## 🔧 Troubleshooting

### "Database not found"
Make sure you've indexed your codebase:
```bash
cgc index /path/to/your/project
```

### Empty Diagrams
Check if your database has data:
```bash
cgc query "MATCH (n) RETURN count(n)"
```

### Large Graphs Too Slow
Limit the results in the queries:
```python
query = """
    MATCH (f:Function)-[:CALLS]->(called:Function)
    RETURN f.name, called.name
    LIMIT 100  # Add this
"""
```

---

## 🌟 Tips & Best Practices

1. **Start with Option C** for a high-level overview
2. **Use Option A** for interactive exploration
3. **Use Option B** for documentation and sharing
4. **Combine multiple views** for comprehensive understanding
5. **Filter large graphs** to focus on specific areas
6. **Export to PNG/SVG** for presentations

---

## 📚 Additional Resources

- [CodeGraphContext Documentation](https://shashankss1205.github.io/CodeGraphContext/)
- [PlantUML Documentation](https://plantuml.com/)
- [Mermaid Documentation](https://mermaid.js.org/)
- [Graphviz Documentation](https://graphviz.org/)
- [Vis.js Network Documentation](https://visjs.github.io/vis-network/docs/network/)

---

## 🤝 Contributing

Have ideas for new visualization types? Found a bug? 

- Open an issue: [GitHub Issues](https://github.com/Shashankss1205/CodeGraphContext/issues)
- Submit a PR: [GitHub Pull Requests](https://github.com/Shashankss1205/CodeGraphContext/pulls)

---

## 📄 License

MIT License - Same as CodeGraphContext

---

**Made with ❤️ for the CodeGraphContext project**
