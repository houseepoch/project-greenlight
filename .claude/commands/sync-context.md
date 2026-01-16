# /sync-context Command

## Purpose
Catch up all context documents from recent work. Ensures documentation reflects current reality.

## Activation
User types: `/sync-context`

## Process

### Step 1: Gather Recent Changes
```
Scan:
- _SESSIONS/CONVERSATION_LOG.md (recent entries)
- _LOGS/CHANGELOG.md (recent changes)
- _LOGS/CHECKPOINTS/ (recent checkpoints)
- src/ (modified files)
```

### Step 2: Identify Stale Context
```
Compare:
- STATE_SNAPSHOT.md vs actual state
- ACTIVE_FOCUS.md vs TODO.md
- TRACE_INDEX vs current traces
```

### Step 3: Update Documents
```
For each stale document:
1. Show current content
2. Show proposed update
3. Ask user to approve ⏸
4. Apply update
5. Log the sync
```

### Step 4: Report
```
SYNC COMPLETE:
✓ Updated: [list of files]
⚠ Needs attention: [any issues]
◆ Current state: [summary]
```

## What Gets Synced

| Document | Sync Source |
|----------|-------------|
| STATE_SNAPSHOT.md | Recent checkpoints + changes |
| ACTIVE_FOCUS.md | TODO.md current task |
| TRACE_INDEX/* | All trace strings in project |
| BLOCKERS.md | Items marked ◈ |
| USER_LEARNING_RECORD.md | Quora interactions |

## User Approval

Each update requires ⏸ approval:
```
📋 SYNC: STATE_SNAPSHOT.md

CURRENT:
[current content summary]

PROPOSED UPDATE:
[new content]

Apply this update? ⏸
```

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●⇄📍
