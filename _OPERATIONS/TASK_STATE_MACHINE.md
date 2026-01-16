# Task State Machine

> **How tasks transition between states.**

---

## STATE DEFINITIONS

```
◇ QUEUED     Task defined, waiting to start
◆ ACTIVE     Currently being worked
◈ BLOCKED    Cannot proceed, waiting on something
◉ COMPLETE   Verified done, user approved
○ SKIPPED    Intentionally bypassed
```

---

## STATE TRANSITIONS

```
                    ┌─────────────────────────────┐
                    │                             │
                    ▼                             │
┌─────┐  select  ┌─────┐  block  ┌─────┐  unblock│
│  ◇  │─────────▶│  ◆  │────────▶│  ◈  │─────────┘
└─────┘          └─────┘         └─────┘
   │                │                │
   │                │                │
   │ skip           │ complete       │ abandon
   │                │                │
   ▼                ▼                ▼
┌─────┐          ┌─────┐          ┌─────┐
│  ○  │          │  ◉  │          │  ◇  │
└─────┘          └─────┘          └─────┘
                   ⏸
              (requires user
               approval)
```

---

## TRANSITION RULES

### ◇ → ◆ (Select)
```
Requirements:
- No ◆ task currently active
- All ⟁ dependencies are ◉
- Scope confirmed ⏸

Actions:
- Log transition to CHANGELOG
- Update ACTIVE_FOCUS.md
- Start checkpoint timer
```

### ◆ → ◉ (Complete)
```
Requirements:
- All acceptance criteria met
- User approval ⏸
- No blockers

Actions:
- Log completion to CHANGELOG
- Archive task details
- Clear ACTIVE_FOCUS.md
- Create checkpoint
```

### ◆ → ◈ (Block)
```
Requirements:
- Identified blocker
- Documented in BLOCKERS.md

Actions:
- Log block reason
- Notify user
- Suggest alternatives if possible
```

### ◈ → ◆ (Unblock)
```
Requirements:
- Blocker resolved
- Documentation updated

Actions:
- Log resolution
- Resume from checkpoint
```

### ◇ → ○ (Skip)
```
Requirements:
- Explicit user request ⏸
- Reason documented

Actions:
- Log skip with reason
- Update dependencies
```

---

## STATE INVARIANTS

```
- Only ONE task can be ◆ at a time
- ◉ requires ⏸ user approval
- ◈ must have documented blocker
- State changes must be logged
```

---

DOCUMENT_STATUS: ●_IMMUTABLE
TRACE: ●◆📍
