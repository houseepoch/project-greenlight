# /status Command

## Purpose
Get a quick report of current project state.

## Activation
User types: `/status`

## Output Format

```
═══════════════════════════════════════════════════
📊 PROJECT STATUS REPORT
═══════════════════════════════════════════════════

🎯 GOAL: [Primary goal summary]
📍 PHASE: [Current phase]
⏱️ LAST CHECKPOINT: [timestamp]

◆ ACTIVE TASK
   ID: [task id]
   Title: [task title]
   Trace: [trace string]
   Progress: [description]

◇ QUEUE ([count] tasks)
   1. [next task]
   2. [following task]

◈ BLOCKED ([count] items)
   - [blocker]: [reason]

✓ RECENTLY COMPLETED
   - [task]: [when]

📝 RECENT CHANGES
   - [change]: [timestamp]

❓ OPEN QUESTIONS
   - [question]

🔮 NEXT ACTIONS
   1. [immediate next]
   2. [following]

MODE: [DEFAULT | QUORA | WALKTHROUGH]
═══════════════════════════════════════════════════
```

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●📍
