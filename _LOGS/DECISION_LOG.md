# Decision Log

> **All significant decisions with rationale. Append only.**

---

## DECISION FORMAT

```
### ⚓[ID]: [Decision Title]

📅 Date: [timestamp]
🔴🟠🟡🟢 Priority: [priority]
📍 Context: [what led to this decision]

**Question:**
[The question that needed answering]

**Options Considered:**
A. [option 1] - [pros/cons]
B. [option 2] - [pros/cons]
C. [option 3] - [pros/cons]

**Decision:**
[What was decided]

**Rationale:**
[Why this option was chosen]

**Implications:**
- [implication 1]
- [implication 2]

**Approved by:** User ⏸ ✓
**Related:** [tasks, docs, etc.]
```

---

## DECISIONS

```
[Entries will be added here]

Example:

### ⚓ARCH-001: REST API Over GraphQL

📅 Date: 2024-01-15T14:30:00Z
🟠 Priority: High
📍 Context: Deciding API architecture

**Question:**
Which API style should we use for the backend?

**Options Considered:**
A. REST - Simple, well-known, easier caching
B. GraphQL - Flexible queries, single endpoint
C. gRPC - Fast, typed, but complex setup

**Decision:**
REST API

**Rationale:**
- Team more familiar with REST
- Simpler caching strategy
- Meets current requirements
- Can migrate later if needed

**Implications:**
- Multiple endpoints to maintain
- May need BFF pattern for mobile
- Standard HTTP caching applies

**Approved by:** User ⏸ ✓
**Related:** T-001, ARCHITECTURE.md
```

---

## DECISION INDEX

| ID | Title | Date | Category | Reversible |
|----|-------|------|----------|------------|
| ⚓ARCH-001 | REST API | 2024-01-15 | Architecture | Yes |

---

## CATEGORIES

```
ARCH    Architecture decisions
TECH    Technology choices
DATA    Data model decisions
UI      User interface decisions
SEC     Security decisions
PROC    Process decisions
```

---

DOCUMENT_STATUS: ◆_LIVE
TRACE: ⚓📍
APPEND_ONLY: true
