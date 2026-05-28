---
name: graphify-query
description: "Uses the graphify utility for semantic search, dependency path discovery, and codebase structure explanation via the project knowledge graph"
---

# graphify-query (Knowledge Graph Queries / Codebase Mapping)

## 🎯 Purpose

This skill instructs the agent on how to use the `graphify` utility for **codebase navigation and semantic query routing**. Instead of costly file scanning or imprecise `grep` searches across code files, the agent queries the local knowledge graph to find relationships, dependencies, and module documentation.

## 🚦 When to Use

- When exploring an unfamiliar codebase or studying a new module.
- To answer questions like "How is component X related to component Y?".
- To understand Software Architecture, locate "god classes", and identify isolated modules.
- After modifying code structure or adding a new file to refresh the graph.

## 📋 Instructions for Execution

The local knowledge graph is stored in the `graphify-out/` directory. The agent can invoke the `graphify` CLI commands:

### 1. Read the Graph Report (Recommended at startup)
Always read the summary report before diving into individual source files:
```bash
cat graphify-out/GRAPH_REPORT.md
```

### 2. Semantic Graph Query (Question Answering)
Find answers to questions about code connections using Breadth-First Search (BFS) graph traversal:
```bash
graphify query "How is user session initialization structured?"
```

### 3. Find Dependency/Connection Path
Find the shortest path of dependencies or call flows between two code symbols/files:
```bash
graphify path "AuthService" "DatabasePool"
```

### 4. Explain an Entity
Get a detailed explanation of a specific entity (class, function, module) and its edges from the graph:
```bash
graphify explain "UserSession"
```

### 5. Update the Graph (Crucial after code changes)
If you edited code or added new files, rebuild the graph (analyses AST, no LLM api calls cost):
```bash
# Update the graph in the current directory:
graphify update .

# Or via the brain CLI utility:
./brain graphify
```

## ⚠️ Safety Rules
- **Graph First:** Always prefer queries like `graphify query` or `graphify path` over slow full-text grep scans.
- **Idempotency:** Re-run `graphify update .` after structural codebase modifications to keep the graph in sync.
- **Ignored Files:** Make sure temporary graph artifacts (`graphify-out/`) are excluded via `.gitignore` and `.graphifyignore`.
