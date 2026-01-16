# /set-project-context Command

## Purpose
Modify the immutable project context. This is a protected operation requiring explicit confirmation.

## Activation
User types: `/set-project-context`

Then either:
- Interactive mode (guided prompts)
- Direct edit: `/set-project-context add [content]`
- Direct edit: `/set-project-context edit [id] [new value]`

## Protection Level: ⏸⏸ (Double Confirmation)

Project context is IMMUTABLE by default. Changes require:
1. Explicit command invocation
2. Showing current value
3. Showing proposed change
4. First confirmation ⏸
5. Second confirmation ⏸⏸
6. Logging the change

## Process

### View Current Context
```
/set-project-context view

Displays:
⚓001: Project Name = [value]
⚓002: Primary Language = [value]
⚓003: Framework = [value]
...
```

### Add New Constant
```
/set-project-context add

Prompts:
1. What constant to add?
2. What is its value?
3. Why is this immutable?

Then requires ⏸⏸ confirmation.
```

### Edit Existing Constant
```
/set-project-context edit ⚓003

Shows:
CURRENT: Framework = React
PROPOSED: Framework = [new value]

Requires:
1. Reason for change
2. ⏸ First confirmation
3. ⏸⏸ Type "CONFIRM EDIT" to proceed
```

## Logging

All changes logged to:
- `_CONTEXT/02_⚓_PROJECT_CONTEXT_IMMUTABLE/PROJECT_CONSTANTS.md` (modification log section)
- `_LOGS/DECISION_LOG.md` (full rationale)

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●⚓⏸📍
