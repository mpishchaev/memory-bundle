# Agent Memory Bundle 🧠

A universal, self-contained, and portable long-term semantic and episodic memory bundle for AI agents (Claude Code, Antigravity, Codex, Hermes, OpenClaw, and others).

It integrates the following into a single system:
1. **Obsidian Vault Folder Structure** based on the PARA + Raw-to-Wiki methodology.
2. **Agent Skills** to let the AI agent work with Obsidian Flavored Markdown, json-canvas, and bases.
3. **Project Knowledge Graph** via the `graphify` utility for semantic codebase navigation and mapping.
4. **Cognitive Automation Scripts** (Sleep Cycle, Maintenance, and index updates).

---

## ⚡ Quick Start

To connect agent memory to a new or existing project:

1. Navigate to your project root:
   ```bash
   cd /path/to/your/project
   ```

2. Run the connection script from this bundle:
   ```bash
   /home/ffazy/Projects/memory-bundle/connect.sh
   ```

3. (Optional) Configure the `.brain/05_Scripts/sleep_cycle/.env` file with your LLM API credentials (required for the Sleep Cycle note parser). You can also define `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) to enable Google Gemini-based semantic enrichment for the Graphify codebase knowledge graph.

---

## 📁 Repository Architecture (PARA)

In the root of the project, a hidden directory `.brain/` is created (folder name can be customized with the `-d` flag), which is a fully functional Obsidian vault:

* **`00_Raw/`** — Ingestion inbox for unstructured notes, chat logs, clipping, and session outputs.
* **`01_Wiki/`** — Long-term semantic knowledge base. Contains subfolders:
  * `concepts/` — abstract ideas, theories, and frameworks.
  * `patterns/` — practical techniques, recipes, and workflows.
  * `technology/` — specific tools, libraries, languages, and vendor APIs.
  * `people/` / `organizations/` — key persons and companies/communities.
  * `sources/` — atomic source citation pages (videos, articles, repositories, threads).
* **`02_Memory/`** — Episodic memory, active contexts, tasks, and session logs.
* **`03_Meta/`** — Vault control panel: `Master_Index.md` (root directory), `hot.md` (current priorities), templates, and the execution log `Log.md`.
* **`04_Archive/`** — Historical data and completed tasks/projects.
* **`05_Scripts/`** — Automation scripts (Python).
* **`06_Skills/`** — Portable agent skills (Agent Skills) symlinked directly to your AI environment.

---

## 🛠️ CLI Interface (`brain`)

After initialization, an executable file `./brain` is created in the project root:

* **`./brain sleep`** — Run the Sleep Cycle. Processes new notes in `00_Raw/`, extracts atomic concepts using LLM, files them under `01_Wiki/` subfolders, and automatically merges duplicates with existing files.
  * Flags: `--limit N` (max raw notes to process), `--archive` (move raw notes to `04_Archive/` instead of marking them consolidated), `--graphify` (rebuild the graph after running), `--dry-run`.
* **`./brain check`** — Run health checks (maintenance). Scans for broken wiki-links, orphan pages, and malformed YAML frontmatter. With `--report`, appends a health report to `Log.md`.
* **`./brain duplicates`** — Scan for near-duplicate concepts in `01_Wiki` using rapidfuzz (similarity threshold configured via `--min N`).
* **`./brain merge --winner <path> --loser <path>`** — Automatically merges a duplicate note into the winner (combining aliases, tags, content, and updating all backlinks in the vault).
* **`./brain index`** — Force regenerate index files (`_index.md`) in all vault folders and recalculate stats.
* **`./brain graphify`** — Quick shortcut to rebuild the codebase relations map via `graphify update`.

---

## 🔗 AI Agent Integrations (Harnesses)

The `connect.sh` script automatically detects and registers the skills in your active AI environments:

1. **Claude Code**: Links skills to `.claude/skills/` and integrates graph rules in `CLAUDE.md`.
2. **Google Antigravity**: Copies skills to `.agents/skills/`.
3. **Codex CLI**: Links skills to `~/.codex/skills/`.
4. **Hermes / OpenCode**: Imports skills to `~/.opencode/skills/memory-bundle/`.

If no agent folder is detected, it defaults to creating `.claude/skills/` locally.

---

## 📊 Navigating the Codebase with Graphify

`graphify` analyzes your code and notes to build a dependency graph. The agent uses the `graphify-query` skill to locate components:
* `graphify query "<question>"` — BFS semantic query across the code graph.
* `graphify path "<SymbolA>" "<SymbolB>"` — trace dependency path/call flows between two components.
* `graphify explain "<Symbol>"` — fetch a detailed description of a symbol's structure and connections.

To visualize the graph, open the generated `graphify-out/graph.html` in a web browser.