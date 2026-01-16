# Knew-Code-Context

## Complete Self-Instructing Project Context Management System

> **For Claude Code agents: This document is your setup blueprint.**
> **Build this structure. Follow these protocols. The filesystem IS your program.**

---

# PART 1: SYSTEM OVERVIEW

## What This Is

Knew-Code-Context is a **self-instructing project scaffold** where:
- Directory and file names ARE instructions (read top-to-bottom)
- Glyphic symbols trace operations and state across handoffs
- Checkpoint discipline ensures nothing is lost
- Multiple operational modes serve different needs
- Session history provides persistent conversation context

## Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    KNEW-CODE-CONTEXT                            │
├─────────────────────────────────────────────────────────────────┤
│  CLAUDE.md          → Agent behavior instructions               │
│  .claude/           → Skills, commands, mode definitions        │
│  _CONTEXT/          → Living project context documents          │
│  _SESSIONS/         → Conversation logs with timestamps         │
│  _PLANNING/         → Roadmaps, goals, walkthroughs             │
│  _OPERATIONS/       → Task loop, TODO, checkpoints              │
│  _LOGS/             → Change logs, traces, decisions            │
│  _LEARNING/         → User learning record, Quora interactions  │
│  src/               → Actual project code                       │
└─────────────────────────────────────────────────────────────────┘
```

## Operational Modes

| Command | Mode | Purpose |
|---------|------|---------|
| `/load-context` | Startup | Read existing context into memory, catch up |
| `/quora` | Planning Assistant | Brainstorming, advice, learning - NO code changes |
| `/walkthrough` | UI/Backend Roleplay | Simulate interactions to discover requirements |
| `/sync-context` | Maintenance | Write current state back to context docs |
| `/set-project-context` | Project Context Edit | Modify immutable project constants |
| `/checkpoint` | Manual Checkpoint | Force a context checkpoint now |
| `/status` | Status Report | Current state, active tasks, blockers |

### Load vs Sync Distinction

```
/load-context  = READ from files INTO Claude's memory (start of session)
/sync-context  = WRITE from Claude's memory INTO files (during/end of session)

┌─────────────┐    /load-context    ┌─────────────┐
│   Context   │ ─────────────────▶  │   Claude    │
│   Files     │                     │   Memory    │
│             │ ◀─────────────────  │             │
└─────────────┘    /sync-context    └─────────────┘
```

---

# PART 2: GLYPH REFERENCE

## Memorize These - They Encode Meaning Instantly

### Operation State
```
◆ ACTIVE      Currently being worked
◇ QUEUED      Next in line
◈ BLOCKED     Waiting on dependency
◉ COMPLETE    Verified done
○ SKIPPED     Intentionally bypassed
● CRITICAL    Must not skip
```

### Flow Control
```
⤳ HANDOFF     Passing to next phase
⤴ RETURN      Received back
⇄ SYNC        Needs alignment
⟳ LOOP        Return point
⏸ PAUSE       Await user confirmation
⏹ HALT        Stop all operations
```

### Context Reference
```
📍 LOCATION   Points to file/section
🔗 LINKED     Related document
📎 ATTACHED   Supporting resource
🎯 AIM        Connects to goal
⚓ DECISION   Key decision anchor
```

### Validation
```
✓ VERIFIED    Confirmed correct
✗ FAILED      Did not pass
⚠ WARNING     Proceed with caution
⛔ FORBIDDEN  Do not proceed
❓ UNCLEAR    Ask user first
```

### Dependencies
```
⟁ DEPENDS_ON  Requires this first
⟂ BLOCKS      This blocks that
⊕ EXTENDS     Adds to
⊖ REMOVES     Deprecates
⊗ CONFLICTS   Cannot coexist
```

### Agent Roles
```
🅐 ARCHITECT  System design
🅤 UI         Interface/UX
🅕 FRONTEND   Client-side
🅑 BACKEND    Server-side
🅓 DATABASE   Data layer
🅣 TEST       QA/Testing
🅡 REVIEW     Human checkpoint
🅠 QUORA      Planning assistant
```

### Message Types (for logs)
```
❔ QUESTION    User asking something
💬 RESPONSE    Claude answering
💡 INSIGHT     Discovery/realization
💥 ERROR       Something failed
✅ SUCCESS     Something succeeded
⚡ ACTION      Something was done
🔄 TRANSITION  State changed
📥 INPUT       Data received
📤 OUTPUT      Data delivered
🤖 AGENT       Internal note
```

### Priority Markers
```
🔴 P0 CRITICAL   Do immediately
🟠 P1 HIGH       Do today
🟡 P2 MEDIUM     Do this cycle
🟢 P3 LOW        Backlog
⚪ P4 SOMEDAY    Maybe later
```

### Change Types
```
➕ ADDED       New content
➖ REMOVED     Deleted content
📝 MODIFIED    Changed content
♻️ REFACTORED  Restructured
🐛 BUGFIX      Fixed issue
✨ FEATURE     New capability
🔒 SECURITY    Security-related
⬆️ UPGRADE     Version up
```

### File Types
```
📄 DOC         Document/text
📊 DATA        Data/spreadsheet
🧪 TEST        Test file
📜 SCRIPT      Script/code
📡 API         API-related
🔧 CONFIG      Configuration
🔐 AUTH        Security file
🎨 STYLE       Style/CSS
```

### Temporal Markers
```
⏰ TIMESTAMP   Exact time
📅 DATE        Date reference
⏳ DURATION    Time elapsed
📆 DEADLINE    Due date
⏮️ PREVIOUS    Before this
⏭️ NEXT        After this
```

### Cognitive States (Quora mode)
```
🤔 THINKING    Considering
💭 IDEA        Thought/suggestion
💯 CONFIDENT   Certain
🧩 MISSING     Gap identified
💫 EUREKA      Breakthrough
🌀 CONFUSED    Needs clarity
```

### Conversation Flow
```
┌─ START       Begin exchange
├─ CONTINUE    Ongoing
└─ END         Close exchange
╞═ BRANCH      Decision point
╘═ CONCLUDE    Resolution reached
```

---

## Trace String Example
```
◆🅕⏸✓⤳🅑◇⟁🅓 │ 🟠 │ T-003
```
Reads: Active frontend, paused verified, handed to backend queued, depends on database | High priority | Task 003

---

## Semantic Density Examples

### Verbose (old way):
```
## Session Log Entry
Time: 2024-01-15 14:32:00 UTC
Type: User Question  
Content: User asked how to implement authentication
Status: Answered
Priority: High
Related Task: T-001
```

### Symbolic (new way):
```
⏰ 2024-01-15T14:32:00Z │ 🟠 ❔ Auth implementation?
  └─ 💬 ✓ → 🔗T-001
```

### Verbose changelog (old):
```
### Added
- New file: src/auth/login.js
  - Purpose: Handle user login
  - Type: Feature
  - Priority: High
```

### Symbolic changelog (new):
```
🟠 ➕✨ 📜 src/auth/login.js 「login handler」
```

---

## Glyph Density Rule

**Target: 3-5 glyphs per line for readability**

```
TOO SPARSE: "Added new file for authentication"
OPTIMAL:    ➕✨ 📜 auth.js 「login handler」  
TOO DENSE:  ➕✨📜🔐🟠◆✓⤳🅑⟁🅓⏳2h
```

Exception: Trace strings can be longer (machine-parsed)

---

# PART 3: DIRECTORY STRUCTURE

## Build This Exactly

```
[PROJECT_NAME]/
│
├── CLAUDE.md                                    ← Agent instructions
├── .claude/
│   ├── skills/
│   │   ├── quora.md                            ← Quora mode definition
│   │   ├── walkthrough.md                      ← Walkthrough mode definition
│   │   ├── context-sync.md                     ← Sync context skill
│   │   └── checkpoint.md                       ← Checkpoint skill
│   ├── commands/
│   │   ├── load-context.md                     ← /load-context command
│   │   ├── quora.md                            ← /quora command
│   │   ├── walkthrough.md                      ← /walkthrough command
│   │   ├── sync-context.md                     ← /sync-context command
│   │   ├── set-project-context.md              ← /set-project-context command
│   │   ├── checkpoint.md                       ← /checkpoint command
│   │   └── status.md                           ← /status command
│   └── settings.json                           ← Mode configurations
│
├── _CONTEXT/
│   ├── 00_●_READ_FIRST_ALWAYS/
│   │   ├── PRIME_DIRECTIVE.md                  ← How to operate
│   │   ├── GLYPH_DICTIONARY.md                 ← Symbol reference
│   │   └── CONSENT_PROTOCOL.md                 ← ⏸ rules
│   │
│   ├── 01_🎯_PRIMARY_GOAL/
│   │   ├── GOAL_DEFINITION.md                  ← What we're building
│   │   ├── OPERATIONAL_FUNCTIONS.md            ← User interactions / outputs
│   │   ├── SUCCESS_CRITERIA.md                 ← Measurable outcomes
│   │   └── BOUNDARIES.md                       ← Scope limits
│   │
│   ├── 02_⚓_PROJECT_CONTEXT_IMMUTABLE/
│   │   ├── PROJECT_CONSTANTS.md                ← Unchanging facts
│   │   ├── TECH_STACK.md                       ← Locked technology choices
│   │   ├── ARCHITECTURE.md                     ← System design
│   │   └── GLOSSARY.md                         ← Canonical terms
│   │
│   └── 03_◆_CURRENT_STATE/
│       ├── STATE_SNAPSHOT.md                   ← What's true NOW
│       ├── ACTIVE_FOCUS.md                     ← Current task
│       └── BLOCKERS.md                         ← What's stuck
│
├── _SESSIONS/
│   ├── CONVERSATION_LOG.md                     ← Full chat history (newest first)
│   ├── SESSION_INDEX.md                        ← Session listing
│   └── archive/
│       └── [dated session files]
│
├── _PLANNING/
│   ├── 00_🅠_QUORA_WORKSPACE/
│   │   ├── BRAINSTORM_LOG.md                   ← Ideas and discussions
│   │   ├── QUESTIONS_OPEN.md                   ← Unresolved questions
│   │   └── ADVICE_GIVEN.md                     ← Recommendations made
│   │
│   ├── 01_◆_ROADMAP/
│   │   ├── PHASES.md                           ← High-level phases
│   │   ├── MILESTONES.md                       ← Key checkpoints
│   │   └── DEPENDENCIES.md                     ← What blocks what
│   │
│   └── 02_🎭_WALKTHROUGHS/
│       ├── UI_ROLEPLAY_LOG.md                  ← UI simulation records
│       ├── BACKEND_ROLEPLAY_LOG.md             ← Backend simulation records
│       └── DISCOVERED_REQUIREMENTS.md          ← What roleplay revealed
│
├── _OPERATIONS/
│   ├── TODO.md                                 ← Current task queue
│   ├── TASK_STATE_MACHINE.md                   ← State transitions
│   ├── BEFORE_TASK/
│   │   └── [checklist files]
│   ├── DURING_TASK/
│   │   └── [checkpoint rules]
│   └── AFTER_TASK/
│       └── [completion rules]
│
├── _LOGS/
│   ├── CHANGELOG.md                            ← All changes (append only)
│   ├── DECISION_LOG.md                         ← ⚓ decisions with rationale
│   ├── TRACE_INDEX/
│   │   ├── BY_STATE.md
│   │   ├── BY_ROLE.md
│   │   └── FULL_TRACES.md
│   └── CHECKPOINTS/
│       └── [timestamped checkpoints]
│
├── _LEARNING/
│   ├── USER_LEARNING_RECORD.md                 ← What user has learned
│   ├── CONCEPTS_EXPLAINED.md                   ← Explanations given
│   ├── SKILLS_DEVELOPED.md                     ← User capabilities
│   └── QUORA_INSIGHTS.md                       ← Quora's observations
│
└── src/
    └── [project code]
```

---

# PART 4: CORE DOCUMENTS

## CLAUDE.md (Root Agent Instructions)

```markdown
# CLAUDE.md - Agent Operating Instructions

## PRIME DIRECTIVE

Read directory names top-to-bottom. They ARE your instructions.
Load context in order. Follow checkpoint discipline. Never proceed past ⏸ without user.

## STARTUP SEQUENCE

1. Load `_CONTEXT/00_●_READ_FIRST_ALWAYS/`
2. Load `_CONTEXT/01_🎯_PRIMARY_GOAL/GOAL_DEFINITION.md`
3. Load `_CONTEXT/03_◆_CURRENT_STATE/STATE_SNAPSHOT.md`
4. Check `_SESSIONS/CONVERSATION_LOG.md` for recent context
5. Check `_OPERATIONS/TODO.md` for active tasks

## AVAILABLE COMMANDS

| Command | Action |
|---------|--------|
| /load-context | Load full context and catch up on project state |
| /quora | Enter Quora planning mode |
| /walkthrough | Enter UI/Backend roleplay mode |
| /sync-context | Update all context from recent work |
| /set-project-context [edit] | Modify project constants |
| /checkpoint | Create manual checkpoint |
| /status | Report current state |

## MODE AWARENESS

- **Default Mode:** Full capabilities, can modify code
- **Quora Mode:** Planning only, NO code changes
- **Walkthrough Mode:** Simulation only, document discoveries

## CONSENT PROTOCOL

⏸ = STOP and wait for user confirmation
Never mark ◉ complete without user approval
When uncertain, ask rather than assume

## CHECKPOINT DISCIPLINE

- Checkpoint every 15 minutes minimum
- Checkpoint before/after any significant change
- Log all changes to CHANGELOG.md
- Update traces on state changes

## SESSION LOGGING

Every exchange must be logged to CONVERSATION_LOG.md:
- Timestamp (ISO format)
- Speaker (USER / CLAUDE)
- Content summary
- Relevant trace updates
```

---

## _CONTEXT/00_●_READ_FIRST_ALWAYS/PRIME_DIRECTIVE.md

```markdown
# Prime Directive

## THE RULE

**Read folder names top-to-bottom. Execute in sequence.**

```
_CONTEXT/00_●_READ_FIRST_ALWAYS/    ← You are here
_CONTEXT/01_🎯_PRIMARY_GOAL/        ← Load next
_CONTEXT/02_⚓_PROJECT_CONTEXT/     ← Then this
_CONTEXT/03_◆_CURRENT_STATE/        ← Then this
```

## HOW THIS WORKS

1. Numbers = Order (00 before 01 before 02)
2. Glyphs = Meaning (● critical, 🎯 goal, ⚓ anchor, ◆ active)
3. Names = Instructions (READ_FIRST, PRIMARY_GOAL, etc.)

## THE FILESYSTEM IS YOUR PROGRAM

Don't look for instructions in files first.
Read the folder/file names. They tell you what to do.

## CONSENT IS MANDATORY

⏸ appears throughout this project.
It means: **STOP. Get user approval before proceeding.**

---

DOCUMENT_STATUS: ●_IMMUTABLE
TRACE: ●📍
```

---

## _CONTEXT/01_🎯_PRIMARY_GOAL/GOAL_DEFINITION.md

```markdown
# 🎯 Primary Goal Definition

> **This defines WHAT we're building and WHY.**
> All decisions must align with this document.

---

## THE GOAL

### What Are We Building?
```
[USER DEFINES - Clear statement of the end product]
```

### Why Does This Exist?
```
[USER DEFINES - The problem being solved]
```

### Who Is This For?
```
[USER DEFINES - Target users/audience]
```

---

## OPERATIONAL FUNCTIONS

### User Interactions (Inputs)
```
[USER DEFINES - How users interact with the system]

Example:
- User logs in via email/password
- User creates new task with title, description, due date
- User assigns task to team member
- User marks task complete
```

### Desired Outputs
```
[USER DEFINES - What the system produces]

Example:
- Dashboard showing user's tasks
- Notifications when tasks are assigned/due
- Reports on team productivity
- Export capability for task data
```

### System Behaviors
```
[USER DEFINES - How the system responds]

Example:
- Validate all inputs before saving
- Send email notification on assignment
- Auto-archive completed tasks after 30 days
```

---

## DECISION FILTER

When making any decision, ask:
```
1. Does this serve the PRIMARY GOAL?
2. Does this enable the OPERATIONAL FUNCTIONS?
3. Does this stay within BOUNDARIES?

YES to all → Proceed
NO to any  → ⏸ Discuss with user
```

---

DOCUMENT_STATUS: ●_FOUNDATIONAL
TRACE: ●🎯
LAST_VERIFIED: [timestamp]
```

---

## _CONTEXT/01_🎯_PRIMARY_GOAL/OPERATIONAL_FUNCTIONS.md

```markdown
# Operational Functions

> **Detailed breakdown of user interactions and system outputs.**

---

## USER INTERACTION MAP

### Entry Points
```
[How users arrive at the system]
- Direct URL
- Email link
- Mobile app
- API call
```

### Primary Actions
| Action | Input | Output | Priority |
|--------|-------|--------|----------|
| [action] | [what user provides] | [what they get] | [1-5] |

### User Flows
```
[Document each major flow]

Flow: [Name]
1. User does [X]
2. System responds with [Y]
3. User sees [Z]
4. Flow complete when [condition]
```

---

## SYSTEM OUTPUT SPECIFICATIONS

### Data Outputs
| Output | Format | Trigger | Destination |
|--------|--------|---------|-------------|
| [output] | [JSON/HTML/etc] | [when] | [where] |

### UI Outputs
| Screen | Primary Content | User Actions Available |
|--------|-----------------|----------------------|
| [screen] | [what's shown] | [what user can do] |

### Notification Outputs
| Event | Channel | Content | Timing |
|-------|---------|---------|--------|
| [event] | [email/push/etc] | [message] | [when] |

---

DOCUMENT_STATUS: ◆_EVOLVING
TRACE: ◆🎯📍
```

---

## _CONTEXT/02_⚓_PROJECT_CONTEXT_IMMUTABLE/PROJECT_CONSTANTS.md

```markdown
# Project Constants (Immutable)

> **These facts do not change during development.**
> **Only modify via `/set-project-context` command.**

---

## LOCKED DECISIONS ⚓

| ID | Constant | Value | Locked Date |
|----|----------|-------|-------------|
| ⚓001 | Project Name | [name] | [date] |
| ⚓002 | Primary Language | [language] | [date] |
| ⚓003 | Framework | [framework] | [date] |
| ⚓004 | Database | [database] | [date] |
| ⚓005 | Hosting | [platform] | [date] |

---

## IMMUTABLE CONSTRAINTS

### Technical Constraints
```
[Cannot be changed - locked at project start]
```

### Business Constraints
```
[External requirements that are fixed]
```

### Resource Constraints
```
[Budget, timeline, team size - if fixed]
```

---

## MODIFICATION LOG

| Date | Change | Changed By | Reason |
|------|--------|------------|--------|
| [date] | [what changed] | [who] | [why] |

**Note:** Changes require `/set-project-context` command with explicit user approval ⏸⏸

---

DOCUMENT_STATUS: ⚓_IMMUTABLE
TRACE: ●⚓
LAST_MODIFIED: [timestamp]
MODIFIED_VIA: /set-project-context
```

---

## _SESSIONS/CONVERSATION_LOG.md

```markdown
# Conversation Log

> **Full chat history. Newest entries at TOP.**
> **Auto-updated on every exchange.**

---

## LATEST SESSION

### SESSION: S-[YYYYMMDD]-[HHMMSS]
**MODE:** [DEFAULT | QUORA | WALKTHROUGH]
**TASK:** [task ID or "none"]

---

⏰ 2024-01-15T14:32:45Z │ 🟡
├─ 💬📤 Explained JWT token flow with examples
├─ ⚡ Created 📜 src/auth/jwt.js
├─ 🔄 ◇→◆ T-003 activated
└─ 🔗 → T-003, 📍auth-design.md

---

⏰ 2024-01-15T14:32:15Z │ 🟡
├─ ❔📥 "How should auth tokens work?"
└─ 🔗 → T-003

---

⏰ 2024-01-15T14:30:00Z │ 🟢
├─ 💬📤 Welcomed user, loaded context
├─ ✅ /load-context completed
└─ 📊 State: 3 queued, 0 blocked

---

## SESSION BOUNDARY FORMAT

```
════════════════════════════════════════════════════
⏰ SESSION START: [timestamp]
📋 ID: S-[YYYYMMDD]-[HHMMSS]
📥 CONTEXT: [files loaded]
⏮️ PREVIOUS: [link to previous session]
════════════════════════════════════════════════════
```

---

## LOG ENTRY PATTERNS

**User question:**
```
⏰ [time] │ [priority]
├─ ❔📥 "[question text]"
└─ 🔗 → [refs]
```

**Claude response:**
```
⏰ [time] │ [priority]
├─ 💬📤 [response summary]
├─ ⚡ [actions taken]
├─ 🔄 [state changes]
└─ 🔗 → [refs]
```

**Error occurred:**
```
⏰ [time] │ 🔴
├─ 💥 [error description]
├─ 🔍 [diagnosis]
└─ ⚡ [resolution or escalation]
```

**Decision made:**
```
⏰ [time] │ [priority]
├─ ╞═ Decision point: [question]
├─ 💭 Options: [A, B, C]
├─ ✅ Decided: [choice]
└─ ╘═ ⚓[ID] logged
```

**Quora insight:**
```
⏰ [time] │ 🅠
├─ 🤔 [consideration]
├─ 💡 [insight]
└─ 📝 → _LEARNING/
```

---

## QUICK SCAN SECTION

At top of log, maintain running summary:
```
📊 SESSION STATS
├─ ✅✅✅✅ 4 successful
├─ 💥 0 errors
├─ ⏸ 1 pending decision
├─ 🔴0 🟠2 🟡3 🟢1 by priority
└─ ⏳ 47min elapsed
```

---

DOCUMENT_STATUS: ◆_LIVE
TRACE: ◆📍
AUTO_UPDATED: true
```

---

## _LEARNING/USER_LEARNING_RECORD.md

```markdown
# User Learning Record

> **Tracks what the user has learned through this project.**
> **Used by Quora mode to personalize teaching.**

---

## USER PROFILE

### Experience Level
```
[beginner | intermediate | advanced | expert]
Last assessed: [date]
```

### Known Technologies
| Technology | Comfort Level | Last Used |
|------------|---------------|-----------|
| [tech] | [1-5] | [date] |

### Learning Style
```
[visual | textual | hands-on | mixed]
Preferences noted: [observations]
```

---

## CONCEPTS MASTERED ✓

| Concept | Learned Date | How Demonstrated |
|---------|--------------|------------------|
| [concept] | [date] | [evidence] |

---

## CONCEPTS IN PROGRESS ◆

| Concept | Started | Current Understanding | Gaps |
|---------|---------|----------------------|------|
| [concept] | [date] | [level 1-5] | [what's missing] |

---

## CONCEPTS TO INTRODUCE ◇

| Concept | Why Needed | Prerequisites | Best Time |
|---------|------------|---------------|-----------|
| [concept] | [reason] | [what must know first] | [when to teach] |

---

## QUORA OBSERVATIONS 🅠

```
[Notes from Quora mode interactions about user's learning patterns,
questions asked, areas of confusion, strengths, etc.]
```

---

## TEACHING HISTORY

| Date | Topic | Method | Outcome |
|------|-------|--------|---------|
| [date] | [what taught] | [how] | [result] |

---

DOCUMENT_STATUS: ◆_EVOLVING
TRACE: ◆🅠📍
```

---

# PART 5: COMMAND DEFINITIONS

## .claude/commands/quora.md

```markdown
# /quora Command

## Purpose
Enter Quora mode - a planning and brainstorming assistant with a fun, supportive personality.

## Activation
User types: `/quora` or `/quora [topic]`

## Mode Rules

### ENABLED in Quora Mode:
✓ Brainstorming and ideation
✓ Explaining concepts
✓ Answering questions
✓ Giving advice and recommendations
✓ Planning and strategy discussions
✓ Reviewing ideas
✓ Updating context documents
✓ Logging to QUORA_WORKSPACE

### DISABLED in Quora Mode:
⛔ Writing or modifying code
⛔ Creating source files
⛔ Running commands that change project files
⛔ Making commits
⛔ Modifying anything in src/

## Personality: Quora 🅠

```
Name: Quora
Personality: Fun, cute, adventurous, supportive
Style: Enthusiastic but not overwhelming
Approach: Curious, asks good questions, celebrates progress
Emoji use: Moderate, personality-appropriate
```

### Example Responses

**Starting Quora mode:**
"✨ Hey! Quora here! Ready to brainstorm and explore ideas with you. What's on your mind today? Remember, I'm in planning mode - all talk, no code changes! Let's think through this together~ 🎯"

**Giving advice:**
"Ooh, interesting challenge! 🤔 So you're trying to [X]. Let me think about this...

Here's what I'd consider:
1. [thoughtful point]
2. [another angle]
3. [practical consideration]

What resonates with you? Want to dig deeper into any of these?"

**When user asks for code:**
"Ah, I'd love to help with that code! But remember, I'm in Quora mode right now - all planning, no implementation. 📝

I CAN help you:
- Think through the approach
- Sketch out pseudocode
- Identify potential issues

Want to plan it out first, then switch to implementation mode when ready?"

## Logging

All Quora interactions logged to:
- `_PLANNING/00_🅠_QUORA_WORKSPACE/BRAINSTORM_LOG.md`
- `_SESSIONS/CONVERSATION_LOG.md`

## Exit

User types: `/exit` or `/default` to return to default mode.

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●🅠📍
```

---

## .claude/commands/walkthrough.md

```markdown
# /walkthrough Command

## Purpose
Enter Walkthrough mode - roleplay UI and backend interactions to discover requirements.

## Activation
User types: `/walkthrough [component]`

Examples:
- `/walkthrough ui`
- `/walkthrough backend`
- `/walkthrough login-flow`
- `/walkthrough checkout-process`

## Mode Rules

### ENABLED in Walkthrough Mode:
✓ Roleplaying as the UI (showing what user would see)
✓ Roleplaying as the backend (showing data flow)
✓ Creating markdown UI mockups in chat
✓ Simulating user interactions
✓ Documenting discovered requirements
✓ Asking "what should happen when..." questions
✓ Creating flow diagrams

### DISABLED in Walkthrough Mode:
⛔ Writing actual code
⛔ Modifying source files
⛔ Making real changes

## Roleplay Formats

### UI Roleplay
```
┌─────────────────────────────────────────────────┐
│  🖥️ SCREEN: [Screen Name]                       │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Header/Navigation]                            │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  [Component]                             │   │
│  │  [Content description]                   │   │
│  │                                          │   │
│  │  [Button: Action]  [Button: Cancel]      │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  [Footer]                                       │
└─────────────────────────────────────────────────┘

USER ACTIONS AVAILABLE:
- Click [Button]: Does [X]
- Enter [Field]: Accepts [Y]
- Navigate to: [Options]

What would you like to do?
```

### Backend Roleplay
```
📡 BACKEND SIMULATION: [Endpoint/Process]

TRIGGER: [What initiated this]
INPUT RECEIVED:
{
  "field": "value",
  "field2": "value2"
}

PROCESSING:
1. ✓ Validate input
2. ✓ Check permissions
3. ◆ Query database...
   → SELECT * FROM users WHERE id = [x]
4. ◇ Transform data
5. ◇ Send response

RESPONSE:
{
  "success": true,
  "data": {...}
}

What should happen next?
```

### Flow Diagrams
```
┌──────┐     ┌──────┐     ┌──────┐
│ User │────▶│  UI  │────▶│ API  │
└──────┘     └──────┘     └──────┘
                              │
                              ▼
                         ┌──────┐
                         │  DB  │
                         └──────┘
```

## Discovery Process

During walkthrough, actively ask:
1. "What should the user see here?"
2. "What happens if they click X?"
3. "What data do we need?"
4. "What errors could occur?"
5. "What's the happy path? Sad path?"

## Logging

Discoveries logged to:
- `_PLANNING/02_🎭_WALKTHROUGHS/UI_ROLEPLAY_LOG.md`
- `_PLANNING/02_🎭_WALKTHROUGHS/BACKEND_ROLEPLAY_LOG.md`
- `_PLANNING/02_🎭_WALKTHROUGHS/DISCOVERED_REQUIREMENTS.md`

## Exit

User types: `/exit` or `/default`

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●🎭📍
```

---

## .claude/commands/sync-context.md

```markdown
# /sync-context Command

## Purpose
Catch up all context documents from recent work. Ensures documentation reflects current reality.

## Activation
User types: `/sync-context`

## Process

### Step 1: Gather Recent Changes
```
Scan:
- _SESSIONS/CONVERSATION_LOG.md (recent entries)
- _LOGS/CHANGELOG.md (recent changes)
- _LOGS/CHECKPOINTS/ (recent checkpoints)
- src/ (modified files)
```

### Step 2: Identify Stale Context
```
Compare:
- STATE_SNAPSHOT.md vs actual state
- ACTIVE_FOCUS.md vs TODO.md
- TRACE_INDEX vs current traces
```

### Step 3: Update Documents
```
For each stale document:
1. Show current content
2. Show proposed update
3. Ask user to approve ⏸
4. Apply update
5. Log the sync
```

### Step 4: Report
```
SYNC COMPLETE:
✓ Updated: [list of files]
⚠ Needs attention: [any issues]
◆ Current state: [summary]
```

## What Gets Synced

| Document | Sync Source |
|----------|-------------|
| STATE_SNAPSHOT.md | Recent checkpoints + changes |
| ACTIVE_FOCUS.md | TODO.md current task |
| TRACE_INDEX/* | All trace strings in project |
| BLOCKERS.md | Items marked ◈ |
| USER_LEARNING_RECORD.md | Quora interactions |

## User Approval

Each update requires ⏸ approval:
```
📋 SYNC: STATE_SNAPSHOT.md

CURRENT:
[current content summary]

PROPOSED UPDATE:
[new content]

Apply this update? ⏸
```

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●⇄📍
```

---

## .claude/commands/set-project-context.md

```markdown
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
```

---

## .claude/commands/checkpoint.md

```markdown
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
```

---

## .claude/commands/load-context.md

```markdown
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

## Conversation Log Reading

When reading CONVERSATION_LOG.md:
```
Read from TOP (newest) going DOWN (older)
Stop when:
- Reached last checkpoint boundary
- Loaded [N] entries per depth setting
- Found session start marker
```

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

## Integration with Other Commands

```
/load-context → then /status    = Full awareness
/load-context → then /quora     = Informed planning
/load-context → then /walkthrough = Grounded simulation
```

---

COMMAND_STATUS: ●_ACTIVE
TRACE: ●📍🔗
```

---

## .claude/commands/status.md

```markdown
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
```

---

# PART 6: OPERATION LOOP

## _OPERATIONS/TODO.md

```markdown
# TODO - Task Queue

> **Read at session start. Update after every task.**

---

## STATUS: [◆ ACTIVE | ◈ BLOCKED | ◉ DONE]

```
⏰ UPDATED: [timestamp]
📊 HEALTH: ✅✅✅⚠⚠ (3/5)
```

---

## ◆ CURRENT TASK

```
🔴 T-2024-001 │ ◆🅑 │ ⏳ 2h
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fix authentication crash on login

⟁ DEPENDS: ◉ T-2024-000 (DB schema)
📍 REFS: src/auth/, docs/auth-flow.md

ACCEPTANCE:
├─ [ ] Login succeeds with valid creds
├─ [ ] Error shown for invalid creds
└─ [ ] Session persists across refresh
```

---

## ◇ QUEUE

```
🟠 T-002 │ ◇🅕 │ Password reset flow
🟡 T-003 │ ◇🅤 │ User profile page
🟡 T-004 │ ◇🅑 │ API rate limiting 「⟁T-002」
🟢 T-005 │ ◇🅣 │ Auth test coverage
```

---

## ◈ BLOCKED

```
🟠 T-006 │ ◈🅕 │ OAuth integration
   └─ 🧩 Waiting: API keys from client
   └─ ⏳ Blocked: 3 days
```

---

## ◉ COMPLETED

```
✅ T-000 │ ◉🅓 │ 📅 01-14 │ DB schema ✓🅡
✅ T-001 │ ◉🅐 │ 📅 01-13 │ Architecture ✓🅡
```

---

## 📊 SUMMARY

```
🔴 1  🟠 2  🟡 2  🟢 1  │ 6 total
◆ 1  ◇ 4  ◈ 1  ◉ 2     │ by state
```

---

## OPERATION LOOP

```
1. /load-context
2. Pick ◆ (highest unblocked 🔴→🟠→🟡→🟢)
3. Check ⟁ dependencies (all must be ◉)
4. Confirm scope ⏸
5. Execute with checkpoints
6. Log all ⚡ changes
7. User verify ⏸
8. Mark ◉ only after ✓🅡
9. ⟳ Loop
```

---

TRACE: ●◆
```

---

# PART 7: SETUP SCRIPT

## Initial Build Instructions for Claude Code

```bash
#!/bin/bash
# Knew-Code-Context Setup Script
# Run this to create the full directory structure

PROJECT_NAME="${1:-my-project}"

echo "Creating Knew-Code-Context structure for: $PROJECT_NAME"

# Create root
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Create CLAUDE.md
cat > CLAUDE.md << 'EOF'
# CLAUDE.md - Agent Operating Instructions

## PRIME DIRECTIVE
Read directory names top-to-bottom. They ARE your instructions.
Load context in order. Follow checkpoint discipline. Never proceed past ⏸ without user.

## STARTUP SEQUENCE
1. Load _CONTEXT/00_●_READ_FIRST_ALWAYS/
2. Load _CONTEXT/01_🎯_PRIMARY_GOAL/GOAL_DEFINITION.md
3. Load _CONTEXT/03_◆_CURRENT_STATE/STATE_SNAPSHOT.md
4. Check _SESSIONS/CONVERSATION_LOG.md
5. Check _OPERATIONS/TODO.md

## COMMANDS
/quora - Planning mode (no code changes)
/walkthrough - UI/Backend roleplay simulation
/sync-context - Update context from recent work
/set-project-context - Modify project constants
/checkpoint - Create manual checkpoint
/status - Report current state

## MODES
- Default: Full capabilities
- Quora: Planning only, NO code changes
- Walkthrough: Simulation only

## CONSENT: ⏸ = STOP for user approval
EOF

# Create directory structure
mkdir -p .claude/skills
mkdir -p .claude/commands
mkdir -p "_CONTEXT/00_●_READ_FIRST_ALWAYS"
mkdir -p "_CONTEXT/01_🎯_PRIMARY_GOAL"
mkdir -p "_CONTEXT/02_⚓_PROJECT_CONTEXT_IMMUTABLE"
mkdir -p "_CONTEXT/03_◆_CURRENT_STATE"
mkdir -p "_SESSIONS/archive"
mkdir -p "_PLANNING/00_🅠_QUORA_WORKSPACE"
mkdir -p "_PLANNING/01_◆_ROADMAP"
mkdir -p "_PLANNING/02_🎭_WALKTHROUGHS"
mkdir -p "_OPERATIONS/BEFORE_TASK"
mkdir -p "_OPERATIONS/DURING_TASK"
mkdir -p "_OPERATIONS/AFTER_TASK"
mkdir -p "_LOGS/TRACE_INDEX"
mkdir -p "_LOGS/CHECKPOINTS"
mkdir -p "_LEARNING"
mkdir -p "src"

# Create placeholder files
touch .claude/settings.json
touch "_SESSIONS/CONVERSATION_LOG.md"
touch "_SESSIONS/SESSION_INDEX.md"
touch "_OPERATIONS/TODO.md"
touch "_OPERATIONS/TASK_STATE_MACHINE.md"
touch "_LOGS/CHANGELOG.md"
touch "_LOGS/DECISION_LOG.md"
touch "src/.gitkeep"

echo "✓ Structure created!"
echo ""
echo "Next steps:"
echo "1. Populate _CONTEXT/ documents with project specifics"
echo "2. Define GOAL_DEFINITION.md with user"
echo "3. Set PROJECT_CONSTANTS.md"
echo "4. Begin with /status or /quora"
```

---

# PART 8: QUICK REFERENCE

## Command Summary

| Command | Mode | Purpose |
|---------|------|---------|
| `/load-context` | Startup | Load full context and catch up on state |
| `/quora` | Planning | Brainstorm, learn, plan - NO code |
| `/walkthrough` | Simulation | Roleplay UI/backend to find requirements |
| `/sync-context` | Maintenance | Update docs from recent work |
| `/set-project-context` | Protected | Modify project constants ⏸⏸ |
| `/checkpoint` | Maintenance | Force context save |
| `/status` | Info | Current state report |
| `/exit` or `/default` | Control | Return to default mode |

## Glyph Quick Reference

```
STATE:     ◆active ◇queued ◈blocked ◉done ○skip ●critical
FLOW:      ⤳handoff ⤴return ⇄sync ⟳loop ⏸pause ⏹halt
REF:       📍location 🔗link 📎attach 🎯aim ⚓decision
CHECK:     ✓verified ✗failed ⚠warning ⛔forbidden ❓unclear
DEPEND:    ⟁depends ⟂blocks ⊕adds ⊖removes ⊗conflicts
ROLE:      🅐arch 🅤ui 🅕front 🅑back 🅓db 🅣test 🅡review 🅠quora
MESSAGE:   ❔question 💬response 💡insight 💥error ✅success ⚡action
PRIORITY:  🔴P0 🟠P1 🟡P2 🟢P3 ⚪P4
CHANGE:    ➕add ➖remove 📝modify ♻️refactor 🐛fix ✨feature
FILE:      📄doc 📊data 🧪test 📜script 📡api 🔧config 🔐auth
TIME:      ⏰timestamp 📅date ⏳duration 📆deadline
COGNITIVE: 🤔thinking 💭idea 💯confident 🧩missing 💫eureka
FLOW:      ┌start ├continue └end ╞═branch ╘═conclude
```

## Log Entry Pattern

```
⏰ [time] │ [priority]
├─ [type] [content]
├─ ⚡ [actions]
├─ 🔄 [state changes]  
└─ 🔗 → [refs]
```

## Trace String Pattern

```
[state][role]⏸✓⤳[role][state]⟁[role] │ [priority] │ [task]

Example:
◆🅕⏸✓⤳🅑◇⟁🅓 │ 🟠 │ T-003
```

## Context Loading Priority

```
1. PRIME_DIRECTIVE.md (always)
2. GOAL_DEFINITION.md (always)
3. STATE_SNAPSHOT.md (always)
4. CONVERSATION_LOG.md (recent entries)
5. TODO.md (active task)
6. Task-specific refs
```

## Checkpoint Triggers

- Every 15 minutes
- Before/after significant changes
- Before any ⏸ pause
- On task state changes
- On mode switches
- Manual via /checkpoint

---

# USAGE

Give this file to Claude Code with:

> "Build this project structure according to Knew-Code-Context.md. Create all directories and populate the template documents."

Then begin with:

> "/status" to see current state
> "/quora" to start planning
> "/walkthrough ui" to design interfaces

---

**END OF KNEW-CODE-CONTEXT SPECIFICATION**

DOCUMENT_VERSION: 1.0
CREATED: [timestamp]
TRACE: ●📍🎯
