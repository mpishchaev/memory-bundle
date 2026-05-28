---
name: vault-git-backup
description: "Creates a commit with changes in the memory vault and pushes them to a remote Git repository for backup"
---

# vault-git-backup (Git Backup / Version Control)

## 💾 Purpose

This skill provides **version control and backups** for the local memory vault using Git. The agent checks the repository status, creates a commit message with a timestamp, and syncs the changes with the remote server.

## 🚦 When to Use

- At the end of a session, after running the Sleep Cycle.
- Before executing large refactorings or merging duplicate notes.
- When requested by the user to establish a checkpoint.

## 📋 Instructions for Execution

Commit and push changes to Git:

```bash
# Invoke via the brain CLI utility (recommended):
./brain backup

# Or directly via Git commands:
git -C .brain add .
git -C .brain commit -m "chore(backup): snapshot $(date +'%Y-%m-%d %H:%M')"
git -C .brain push origin main
```
