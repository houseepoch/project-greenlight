# Checkpoint Rules

> **When and how to create checkpoints during task execution.**

---

## CHECKPOINT TRIGGERS

### Time-Based
```
⏰ Every 15 minutes of active work
```

### Event-Based
```
⚡ Before significant file changes
⚡ After significant file changes
🔄 On state transitions
⏸ Before any pause for user input
💥 After recovering from errors
📝 After important decisions
```

---

## CHECKPOINT CREATION

### Quick Checkpoint
```
For routine time-based checkpoints:
1. Note current position
2. Log to CONVERSATION_LOG.md
3. Continue work
```

### Full Checkpoint
```
For significant events:
1. Create checkpoint file
2. Update STATE_SNAPSHOT.md
3. Log to CHANGELOG.md
4. Update traces
```

---

## CHECKPOINT CONTENT

```markdown
# Checkpoint: CP-[YYYYMMDD]-[HHMMSS]

## State
- TASK: [active task]
- PROGRESS: [where in task]
- TRACE: [current trace]

## Since Last Checkpoint
- Changes: [list]
- Decisions: [list]

## Next Steps
- [immediate next]
- [following]

## Recovery
To resume: [instructions]
```

---

## CHECKPOINT DISCIPLINE

```
DO:
✓ Checkpoint before risky operations
✓ Checkpoint after successful milestones
✓ Keep checkpoints concise
✓ Make recovery instructions clear

DON'T:
✗ Skip checkpoints to save time
✗ Checkpoint mid-operation
✗ Leave checkpoints without recovery info
```

---

DOCUMENT_STATUS: ●_REFERENCE
TRACE: ●◆📍
