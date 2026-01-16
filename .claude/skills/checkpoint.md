# Checkpoint Skill Definition

## Skill: Context Checkpointing

### Purpose
Create recoverable snapshots of project state.

### Triggers
- Every 15 minutes (automatic)
- Before/after significant changes
- Before ⏸ pauses
- On task state transitions
- On mode switches
- Manual via `/checkpoint`

### Checkpoint Contents

```markdown
# Checkpoint: CP-[YYYYMMDD]-[HHMMSS]

## State
- PHASE: [current phase]
- TASK: [active task ID and title]
- MODE: [DEFAULT | QUORA | WALKTHROUGH]
- TRACE: [current trace string]

## Recent Changes (since last checkpoint)
- [timestamp] [change description]

## Context Snapshot
- Goal alignment: [OK | DRIFT]
- Blockers: [list or "none"]
- Next actions: [list]

## Open Questions
- [questions awaiting user response]

## Recovery Instructions
To resume from this checkpoint:
1. Load these files: [list]
2. Current task is: [task]
3. Next step is: [action]
```

### File Location
`_LOGS/CHECKPOINTS/CP-[YYYYMMDD]-[HHMMSS].md`

### Related Updates
When checkpoint created, also update:
- STATE_SNAPSHOT.md (summary)
- CONVERSATION_LOG.md (checkpoint marker)
- CHANGELOG.md (if changes occurred)

---

SKILL_STATUS: ●_ACTIVE
