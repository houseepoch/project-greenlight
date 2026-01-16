# /checkpoint Command

## Purpose
Force an immediate context checkpoint.

## Activation
User types: `/checkpoint` or `/checkpoint [note]`

## Process

1. Capture current state:
   - Active task
   - Recent changes
   - Current traces
   - Open questions

2. Create checkpoint file:
   `_LOGS/CHECKPOINTS/CP-[YYYYMMDD]-[HHMMSS].md`

3. Update documents:
   - STATE_SNAPSHOT.md
   - CONVERSATION_LOG.md
   - CHANGELOG.md

4. Confirm to user:
   ```
   ✓ CHECKPOINT CREATED
   ID: CP-20240115-143215
   State: [summary]
   Changes since last: [list]
   ```

## Checkpoint Contents

```markdown
# Checkpoint: CP-[timestamp]

## State
- PHASE: [current phase]
- TASK: [active task]
- MODE: [current mode]
- TRACE: [current trace string]

## Recent Changes
- [change 1]
- [change 2]

## Context Snapshot
- Goal alignment: [OK/DRIFT]
- Blockers: [list or none]
- Next actions: [list]

## Open Questions
- [questions awaiting answers]

## Recovery Instructions
To resume from this checkpoint:
1. Load [files]
2. Current task is [X]
3. Next step is [Y]
```

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●✓📍
