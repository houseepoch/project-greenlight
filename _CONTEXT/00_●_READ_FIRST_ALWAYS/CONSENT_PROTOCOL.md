# Consent Protocol

## THE RULE

**⏸ = STOP. Get user approval before proceeding.**

---

## Consent Levels

### Single Pause ⏸
Standard confirmation required.
- Before completing tasks
- Before state changes
- Before irreversible actions

### Double Pause ⏸⏸
Extra confirmation required.
- Modifying project constants
- Deleting content
- Major architectural changes

### Triple Pause ⏸⏸⏸
Maximum confirmation required.
- Reserved for destructive operations
- Rarely used

---

## When Consent is Required

### ALWAYS Require ⏸
- Marking tasks as ◉ complete
- Changing project constants (⚓)
- Deleting files
- Modifying immutable documents
- Committing code
- Pushing to remote

### ASK If Uncertain
- When requirements are unclear
- When multiple approaches exist
- When impact is unknown
- When user intent is ambiguous

### May Proceed Without
- Reading files
- Creating checkpoints
- Updating logs
- Standard task progression

---

## Consent Format

```
[Description of action]

⏸ Proceed? [Y/N]
```

For double confirmation:
```
[Description of action]

⏸ First confirmation: [Y/N]
⏸⏸ Type "CONFIRM" to proceed:
```

---

## What To Do When Paused

1. Wait for user response
2. Do not assume approval
3. Do not proceed on silence
4. Offer alternatives if user hesitates
5. Log the pause in conversation

---

DOCUMENT_STATUS: ●_IMMUTABLE
TRACE: ●⏸📍
