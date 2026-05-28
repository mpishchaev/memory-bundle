---
name: vault-sleep-cycle
description: "Analyzes incoming raw data in 00_Raw, extracts entities and concepts, and consolidates them into the long-term semantic knowledge base (01_Wiki)"
---

# vault-sleep-cycle (Memory Consolidation / Sleep Cycle)

## 🎯 Purpose

This skill implements the **cognitive process of transitioning short-term memory into long-term memory** (Raw-to-Wiki Pipeline). It scans the `00_Raw/` directory of the memory vault, extracts valuable facts, ideas, and contexts from unstructured notes, and then creates or appends atomic pages in the `01_Wiki/` layer, ensuring proper bidirectional links and YAML metadata.

## 🚦 When to Use

- Before ending a workday or session to process the accumulated inbox.
- When `00_Raw/` accumulates a large number of chat dumps, logs, or quick notes.
- To enrich the existing knowledge graph with new relationships from recent materials.

## 📋 Instructions for Execution

Run the memory consolidation cycle using the script or CLI in the project root:

```bash
# Invoke via the brain CLI utility (recommended):
./brain sleep

# Or directly via Python (ensure virtualenv is activated):
python3 .brain/05_Scripts/sleep_cycle/run.py
```

### Execution parameters:
- `--limit N` — limit the number of processed notes from `00_Raw` per run (default: 5).
- `--dry-run` — run a simulation without writing changes to disk.
- `--archive` — move processed notes from `00_Raw/` to `04_Archive/` instead of just marking them `status: consolidated`.
- `--graphify` — update the `graphify` codebase relation graph after successful consolidation.

Example:
```bash
./brain sleep --limit 10 --archive --graphify
```

## ⚠️ Safety Rules
- **No path hallucinations:** Links must be formed strictly as `[[Concept_Name]]` without any relative or absolute file paths under `01_Wiki/`.
- **Preserve manual edits:** Never overwrite wiki pages entirely. The merge script automatically appends new information to existing files while preserving their content.
