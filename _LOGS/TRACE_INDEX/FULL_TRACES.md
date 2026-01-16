# Full Traces

> **Complete trace strings for all tracked items.**

---

## TRACE FORMAT

```
[state][role]⏸✓⤳[role][state]⟁[role] │ [priority] │ [id]

Components:
- State: ◆◇◈◉○●
- Role: 🅐🅤🅕🅑🅓🅣🅡🅠
- Flow: ⤳handoff ⤴return ⇄sync
- Depend: ⟁depends ⟂blocks
- Check: ✓verified ⏸paused
```

---

## CURRENT TRACES

```
[Active trace strings]

Example:
◆🅑⟁🅓 │ 🟠 │ T-001
  └─ Active backend task, depends on database, high priority

◇🅕⟁◉🅑 │ 🟡 │ T-002
  └─ Queued frontend, depends on completed backend, medium priority

◈🅕⏸❓ │ 🟠 │ T-006
  └─ Blocked frontend, paused unclear, high priority
```

---

## TRACE HISTORY

```
[Historical traces showing progression]

T-001:
├─ ◇🅑 │ Created
├─ ◆🅑⟁🅓 │ Activated, depends on DB
├─ ◆🅑⏸ │ Paused for review
├─ ◆🅑✓ │ Review passed
└─ ◉🅑✓🅡 │ Complete, reviewed

T-002:
├─ ◇🅕 │ Created
├─ ◇🅕⟁◇🅑 │ Waiting on backend
└─ ◇🅕⟁◉🅑 │ Backend done, ready to start
```

---

## READING TRACES

### Quick Scan
```
First glyph = current state
Last segment = priority and ID
Middle = dependencies and flow
```

### Example Decode
```
◆🅕⏸✓⤳🅑◇⟁🅓 │ 🟠 │ T-003

◆🅕       = Active frontend
⏸✓       = Paused, then verified
⤳🅑◇     = Handed to backend (queued)
⟁🅓      = Depends on database
🟠       = High priority
T-003    = Task ID
```

---

DOCUMENT_STATUS: ◆_LIVE
TRACE: ◆📍
