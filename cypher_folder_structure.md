# Cypher Queries for Folder/File Structure Visualization

## 1. View the Complete Hierarchy (Repository → Directory → File)

```cypher
// Show Repository → Directory → File hierarchy
MATCH path = (r:Repository)-[:CONTAINS*]->(n)
WHERE n:Directory OR n:File
RETURN path
```

## 2. View Only Repository, Directory, and File Nodes

```cypher
// Return only Repository, Directory, and File nodes with their relationships
MATCH (r:Repository)
OPTIONAL MATCH (r)-[:CONTAINS]->(d:Directory)
OPTIONAL MATCH (d)-[:CONTAINS]->(f:File)
OPTIONAL MATCH (r)-[:CONTAINS]->(f2:File)
RETURN r, d, f, f2
```

## 3. Hierarchical Tree Structure (Text Output)

```cypher
// Show hierarchical structure with paths
MATCH (r:Repository)
OPTIONAL MATCH (r)-[:CONTAINS]->(d:Directory)
OPTIONAL MATCH (d)-[:CONTAINS]->(f:File)
RETURN 
  r.name as Repository,
  d.path as Directory,
  collect(DISTINCT f.name) as Files
ORDER BY r.name, d.path
```

## 4. Clean Up - Remove All Non-File/Directory/Repository Nodes

**⚠️ WARNING: This will delete all Function, Class, Variable, Module, Parameter nodes!**

```cypher
// Delete all nodes that are NOT Repository, Directory, or File
MATCH (n)
WHERE NOT (n:Repository OR n:Directory OR n:File)
DETACH DELETE n
```

## 5. Safe Cleanup - Remove Only Orphaned Nodes

```cypher
// Remove nodes that have no connections to Repository/Directory/File
MATCH (n)
WHERE NOT (n:Repository OR n:Directory OR n:File)
  AND NOT EXISTS((n)-[]-(:Repository))
  AND NOT EXISTS((n)-[]-(:Directory))
  AND NOT EXISTS((n)-[]-(:File))
DETACH DELETE n
```

## 6. View Statistics Before Cleanup

```cypher
// Count nodes by type
MATCH (n)
RETURN labels(n)[0] as NodeType, count(*) as Count
ORDER BY Count DESC
```

## 7. Simplified Visualization Query (For Neo4j Browser)

```cypher
// Best for visualization in Neo4j Browser
MATCH (r:Repository)-[:CONTAINS*0..2]->(n)
WHERE n:Repository OR n:Directory OR n:File
RETURN r, n
LIMIT 100
```

## 8. Export Folder Structure as JSON

```cypher
// Get hierarchical structure as nested JSON
MATCH (r:Repository)
OPTIONAL MATCH (r)-[:CONTAINS]->(d:Directory)
OPTIONAL MATCH (d)-[:CONTAINS]->(f:File)
WITH r, d, collect({name: f.name, path: f.path}) as files
WITH r, collect({path: d.path, files: files}) as directories
RETURN {
  repository: r.name,
  path: r.path,
  directories: directories
} as structure
```

## 9. Count Files per Directory

```cypher
// Show how many files are in each directory
MATCH (d:Directory)-[:CONTAINS]->(f:File)
RETURN d.path as Directory, count(f) as FileCount
ORDER BY FileCount DESC
```

## 10. Find Root Directories (Direct children of Repository)

```cypher
// Show only top-level directories
MATCH (r:Repository)-[:CONTAINS]->(d:Directory)
WHERE NOT EXISTS((d)<-[:CONTAINS]-(:Directory))
RETURN r.name as Repository, collect(d.path) as RootDirectories
```

## Usage Instructions

### For Visualization (like your image):

1. **In Neo4j Browser:**
   ```cypher
   MATCH (r:Repository)-[:CONTAINS*0..3]->(n)
   WHERE n:Repository OR n:Directory OR n:File
   RETURN r, n
   LIMIT 200
   ```

2. **Using cgc CLI:**
   ```bash
   python3 -c "import sys; sys.path.insert(0, 'src'); from codegraphcontext.cli.main import app; app(['query', 'MATCH (r:Repository)-[:CONTAINS*0..3]->(n) WHERE n:Repository OR n:Directory OR n:File RETURN r, n LIMIT 200'])"
   ```

### To Clean Up Extra Nodes:

**Option A: Remove EVERYTHING except Repository/Directory/File**
```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from codegraphcontext.cli.main import app; app(['query', 'MATCH (n) WHERE NOT (n:Repository OR n:Directory OR n:File) DETACH DELETE n'])"
```

**Option B: Keep code nodes but remove orphans**
```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from codegraphcontext.cli.main import app; app(['clean'])"
```

### To Visualize in Browser:

```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from codegraphcontext.cli.main import app; app(['visualize'])"
```

Then paste Query #7 in the Neo4j Browser.
