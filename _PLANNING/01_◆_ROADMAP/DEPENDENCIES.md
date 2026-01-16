# Dependencies

> **What blocks what. Critical path mapping.**

---

## DEPENDENCY GRAPH

```
                    ┌─────────┐
                    │ T-001   │
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ T-002   │ │ T-003   │ │ T-004   │
         └────┬────┘ └────┬────┘ └─────────┘
              │          │
              └────┬─────┘
                   ▼
              ┌─────────┐
              │ T-005   │
              └─────────┘
```

---

## DEPENDENCY LIST

### ⟁ DEPENDS ON (needs to complete first)

| Task | Depends On | Reason |
|------|------------|--------|
| T-002 | T-001 | [why] |
| T-003 | T-001 | [why] |
| T-005 | T-002, T-003 | [why] |

### ⟂ BLOCKS (prevents others from starting)

| Task | Blocks | Impact |
|------|--------|--------|
| T-001 | T-002, T-003, T-004 | [impact] |

### ⊗ CONFLICTS (cannot coexist)

| Task A | Task B | Reason |
|--------|--------|--------|
| [task] | [task] | [why they conflict] |

---

## CRITICAL PATH

```
The longest chain of dependencies:
T-001 → T-002 → T-005 → T-007 → ...

Total tasks in critical path: [count]
```

---

## DEPENDENCY HEALTH

```
✓ Clear dependencies: [count]
⚠ Circular risk: [none | list]
◈ Blocked tasks: [count]
```

---

DOCUMENT_STATUS: ◆_EVOLVING
TRACE: ◆⟁📍
