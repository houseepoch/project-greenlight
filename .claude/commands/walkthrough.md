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
