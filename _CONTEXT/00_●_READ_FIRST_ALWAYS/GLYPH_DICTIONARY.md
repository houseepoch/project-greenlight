# Glyph Dictionary

> **Quick reference for all symbolic notation used in this project.**

---

## Operation State
```
◆ ACTIVE      Currently being worked
◇ QUEUED      Next in line
◈ BLOCKED     Waiting on dependency
◉ COMPLETE    Verified done
○ SKIPPED     Intentionally bypassed
● CRITICAL    Must not skip
```

## Flow Control
```
⤳ HANDOFF     Passing to next phase
⤴ RETURN      Received back
⇄ SYNC        Needs alignment
⟳ LOOP        Return point
⏸ PAUSE       Await user confirmation
⏹ HALT        Stop all operations
```

## Context Reference
```
📍 LOCATION   Points to file/section
🔗 LINKED     Related document
📎 ATTACHED   Supporting resource
🎯 AIM        Connects to goal
⚓ DECISION   Key decision anchor
```

## Validation
```
✓ VERIFIED    Confirmed correct
✗ FAILED      Did not pass
⚠ WARNING     Proceed with caution
⛔ FORBIDDEN  Do not proceed
❓ UNCLEAR    Ask user first
```

## Dependencies
```
⟁ DEPENDS_ON  Requires this first
⟂ BLOCKS      This blocks that
⊕ EXTENDS     Adds to
⊖ REMOVES     Deprecates
⊗ CONFLICTS   Cannot coexist
```

## Agent Roles
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

## Message Types
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

## Priority Markers
```
🔴 P0 CRITICAL   Do immediately
🟠 P1 HIGH       Do today
🟡 P2 MEDIUM     Do this cycle
🟢 P3 LOW        Backlog
⚪ P4 SOMEDAY    Maybe later
```

## Change Types
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

## File Types
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

## Temporal Markers
```
⏰ TIMESTAMP   Exact time
📅 DATE        Date reference
⏳ DURATION    Time elapsed
📆 DEADLINE    Due date
⏮️ PREVIOUS    Before this
⏭️ NEXT        After this
```

## Cognitive States (Quora mode)
```
🤔 THINKING    Considering
💭 IDEA        Thought/suggestion
💯 CONFIDENT   Certain
🧩 MISSING     Gap identified
💫 EUREKA      Breakthrough
🌀 CONFUSED    Needs clarity
```

## Conversation Flow
```
┌─ START       Begin exchange
├─ CONTINUE    Ongoing
└─ END         Close exchange
╞═ BRANCH      Decision point
╘═ CONCLUDE    Resolution reached
```

---

## Trace String Format

```
[state][role]⏸✓⤳[role][state]⟁[role] │ [priority] │ [task]

Example:
◆🅕⏸✓⤳🅑◇⟁🅓 │ 🟠 │ T-003
```

Reads: Active frontend, paused verified, handed to backend queued, depends on database | High priority | Task 003

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

DOCUMENT_STATUS: ●_IMMUTABLE
TRACE: ●📍
