---
name: vault-maintenance
description: "Performs vault health checks: searches for broken links, orphan pages, and validates YAML metadata"
---

# vault-maintenance (Vault Maintenance / Health Check)

## 🛠️ Purpose

This skill is designed to **maintain order and connectivity in the knowledge base** (Graph Integrity). Over time, the knowledge graph can develop broken links (pointing to non-existent files), orphan pages (with no incoming or outgoing links), and notes with malformed or missing YAML Frontmatter. The `vault-maintenance` skill scans the `01_Wiki/` and `02_Memory/` layers to detect and resolve these anomalies.

## 🚦 When to Use

- As part of regular vault hygiene (e.g., at the end of the week).
- After bulk importing or manual renaming/moving of files.
- When you suspect degradation of context (losing links between related topics).

## 📋 Instructions for Execution

Run the memory health check using the following command:

```bash
# Invoke via the brain CLI utility (recommended):
./brain check --report

# Or directly via Python:
python3 .brain/05_Scripts/maintenance/check.py --report
```

### Additional Maintenance Tools:
The script also supports scanning for and merging duplicate concepts.

1. **Find duplicates:**
   ```bash
   # Find concepts with similar names or aliases (default similarity threshold is 85):
   python3 .brain/05_Scripts/maintenance/find_duplicates.py --min 80
   ```

2. **Merge duplicates:**
   ```bash
   # Merges a duplicate concept into the winner (transfers aliases, tags, content, and updates all backlinks in the vault):
   python3 .brain/05_Scripts/maintenance/merge_duplicates.py --winner .brain/01_Wiki/concepts/Main_Concept.md --loser .brain/01_Wiki/concepts/Duplicate_Concept.md
   ```
