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

## GLYPH QUICK REFERENCE

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
```

---

DOCUMENT_STATUS: ●_IMMUTABLE
TRACE: ●📍
