# Context Sync Skill Definition

## Skill: Context Synchronization

### Purpose
Keep all context documents aligned with current project state.

### Triggers
- Manual via `/sync-context`
- After significant changes
- Before session end
- When stale context detected

### Sync Process

1. **Scan Sources**
   - Recent conversation log entries
   - Changelog entries
   - Checkpoint files
   - Modified source files

2. **Identify Drift**
   - Compare documented state vs actual state
   - Find stale timestamps
   - Detect orphaned references

3. **Propose Updates**
   - Show current vs proposed
   - Explain what changed
   - Wait for approval ⏸

4. **Apply Changes**
   - Update documents
   - Log the sync
   - Update traces

### Documents Synced

| Document | Update Frequency |
|----------|------------------|
| STATE_SNAPSHOT.md | Every sync |
| ACTIVE_FOCUS.md | When task changes |
| TRACE_INDEX/* | When traces update |
| BLOCKERS.md | When blocks change |

### Approval Required
All sync operations require user approval before applying changes.

---

SKILL_STATUS: ●_ACTIVE
