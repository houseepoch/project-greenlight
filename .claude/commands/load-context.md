# /load-context Command

## Purpose
Explicitly load full project context and catch up on current state. This is the "start of session" command that ensures Claude has complete awareness.

## Activation
User types: `/load-context` or `/load-context [depth]`

Depth options:
- `/load-context` - Standard load (recent context)
- `/load-context full` - Complete load (all history)
- `/load-context quick` - Minimal load (just essentials)
- `/load-context since [date/checkpoint]` - Load from specific point

## Process

### Phase 1: Core Context Load ●
```
Loading essential context...

1. ✓ _CONTEXT/00_●_READ_FIRST_ALWAYS/PRIME_DIRECTIVE.md
2. ✓ _CONTEXT/01_🎯_PRIMARY_GOAL/GOAL_DEFINITION.md
3. ✓ _CONTEXT/01_🎯_PRIMARY_GOAL/OPERATIONAL_FUNCTIONS.md
4. ✓ _CONTEXT/02_⚓_PROJECT_CONTEXT_IMMUTABLE/PROJECT_CONSTANTS.md
5. ✓ _CONTEXT/03_◆_CURRENT_STATE/STATE_SNAPSHOT.md
```

### Phase 2: Session History Load 📜
```
Loading conversation history...

1. ✓ _SESSIONS/CONVERSATION_LOG.md (last [N] entries)
2. ✓ _SESSIONS/SESSION_INDEX.md (session boundaries)
3. ◆ Identifying last checkpoint...
4. ◆ Loading changes since checkpoint...
```

### Phase 3: Operations Load ◆
```
Loading operational state...

1. ✓ _OPERATIONS/TODO.md
2. ✓ _LOGS/CHANGELOG.md (recent entries)
3. ✓ _LOGS/CHECKPOINTS/[latest].md
4. ◆ Rebuilding trace state...
```

### Phase 4: Catch-Up Analysis 🔍
```
Analyzing what happened since last session...

LAST SESSION: [timestamp]
LAST CHECKPOINT: [checkpoint ID]

CHANGES SINCE THEN:
- [change 1]
- [change 2]

DECISIONS MADE:
- ⚓[ID]: [decision]

TASKS COMPLETED:
- ◉ [task]

CURRENT STATE:
- Active: [task]
- Blocked: [items]
- Queue: [count] tasks
```

### Phase 5: Ready Report ✓
```
═══════════════════════════════════════════════════
✓ CONTEXT LOADED
═══════════════════════════════════════════════════

🎯 PROJECT: [name]
📍 GOAL: [primary goal summary]

📊 LOADED:
   • Core context: [X] files
   • Session history: [Y] entries
   • Checkpoints: [Z] reviewed

⏱️ CAUGHT UP TO: [timestamp]
🔄 LAST CHECKPOINT: [checkpoint ID]

◆ CURRENT FOCUS:
   Task: [active task]
   Status: [status]
   Trace: [trace string]

◇ READY FOR:
   1. [suggested next action]
   2. [alternative action]

💡 CONTEXT NOTES:
   - [any important observations]
   - [any gaps or questions]

MODE: [DEFAULT | QUORA | WALKTHROUGH]
═══════════════════════════════════════════════════

What would you like to do? ⏸
```

## Depth Options Detail

### Quick Load (`/load-context quick`)
```
Loads ONLY:
- GOAL_DEFINITION.md
- STATE_SNAPSHOT.md
- TODO.md
- Last 5 conversation entries

Use when: Quick task, context mostly known
```

### Standard Load (`/load-context`)
```
Loads:
- All core context (Phase 1)
- Last 20 conversation entries
- Last 3 checkpoints
- Recent changelog entries

Use when: Normal session start
```

### Full Load (`/load-context full`)
```
Loads:
- ALL context files
- ALL conversation history
- ALL checkpoints
- Complete trace index
- User learning record
- Quora workspace

Use when: Long break, need complete picture
```

### Since Load (`/load-context since CP-20240115-120000`)
```
Loads:
- Core context
- Everything AFTER specified checkpoint
- Changes, decisions, conversations since then

Use when: Resuming from known point
```

## Automatic Triggers

Context load automatically suggested when:
- New session detected (gap > 1 hour)
- User seems to lack context
- References to unknown tasks/decisions
- After mode switches

## Context Gaps Detection

During load, identify and report:
```
⚠️ CONTEXT GAPS DETECTED:

1. STATE_SNAPSHOT.md last updated [old date]
   → May be stale, recommend /sync-context

2. Task T-xxx referenced but not in TODO.md
   → Possible orphan, needs review

3. Trace string mismatch found
   → [file] trace doesn't match index

Resolve gaps? ⏸
```

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●📍🔗
