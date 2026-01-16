# Changelog

> **All changes to the project. Append only. Newest at TOP.**

---

## FORMAT

```
📅 [DATE]

[priority] [change-type] [file-type] [path] 「[description]」
└─ 🔗 [task-id] │ [trace]
```

---

## CHANGES

```
[DATE] 2026-01-15 - Image Generation + UI Fixes (Session 2)

[P1] [MOD] [CODE] greenlight/core/image_gen.py - Image generation improvements
|- Fixed Replicate auth: export token to os.environ
|- Fixed FileOutput handling for newer replicate library
|- Added MEDIA_TYPE_STYLES dict for style reinforcement
|- Changed default model: p_image_edit → flux_2_pro

[P1] [MOD] [CODE] greenlight/core/config.py - Default model change
|- default_image_model: "flux_2_pro"

[P1] [MOD] [CODE] greenlight/pipelines/references.py - Style templates
|- Added MEDIA_TYPE_STYLES and get_media_style_prompt()
|- Updated prompt templates with {media_style_prompt}
|- Changed default model to flux_2_pro

[P1] [MOD] [CODE] greenlight/pipelines/storyboard.py - Style integration
|- Import get_media_style_prompt from image_gen
|- Updated _build_style_suffix() to use media templates

[P2] [MOD] [UI] web/src/components/views/world-view.tsx - Reference generation
|- Removed ReferenceModal usage from EntityCard
|- Added simple "Generate Reference" button
|- Added isGenerating state and handleGenerateReference()

[P2] [MOD] [CONFIG] web/package.json - Tailwind downgrade
|- Downgraded Tailwind 4 → Tailwind 3 (compatibility issues)

[P3] [ADD] [GIT] Initial commit pushed to GitHub
|- https://github.com/houseepoch/project-greenlight

---

[DATE] 2026-01-15 - Outline Generator Feature

[P1] [ADD] [CODE] greenlight/pipelines/outline_generator.py - 3-variant story outline generator
|- OUTLINE-001 | COMPLETE
|- Dramatic Arc: Classic three-act structure
|- Mystery Unfolding: Revelation-based progression
|- Character Journey: Internal transformation focus

[P1] [ADD] [API] greenlight/api/pipelines.py - Outline generator endpoints
|- /outline-generator - Generate 3 variants
|- /outlines/{path} - Get variants
|- /outlines/select - Select variant for editing
|- /outlines/update-beats - Save edited beats
|- /outlines/confirm - Confirm and save for Director

[P1] [ADD] [UI] web/src/components/modals/outline-modal.tsx - Outline selection/editing modal
|- Tabbed variant display
|- Beat editing (add/remove/reorder)
|- Confirm flow to Director

[P2] [MOD] [UI] web/src/components/header.tsx - Added Outline button, wired modal flow
|- Ingest -> Entity Confirm -> World Builder -> Outline -> Director

[P2] [ADD] [TEST] test_outline_generator.py - Outline generator test script
|- TEST PASSED: 14/14/13 beats generated

---

[DATE] 2026-01-14 - Integration Testing Complete

[P2] [ADD] [TEST] test_ingestion.py - Ingestion pipeline test script
|- TEST-001 | PASS

[P2] [ADD] [TEST] test_world_builder.py - World builder pipeline test script
|- TEST-001 | PASS

[P2] [ADD] [DATA] test_project/pitch.md - Test pitch: The Flower and the Courtesan
|- TEST-001 | PASS

[P2] [ADD] [DATA] test_project/ingestion/confirmed_entities.json - Confirmed entities with canonical tags
|- TEST-001 | PASS

[P3] [MOD] [CODE] greenlight/pipelines/world_builder.py - Removed Unicode warning symbol
|- TEST-001 | PASS

[P3] [MOD] [DOC] _CONTEXT/03_STATE/STATE_SNAPSHOT.md - Removed Unicode, updated test status
|- TEST-001 | PASS

TEST RESULTS:
- Ingestion: PASSED (6 chars, 5 locations, 13 props extracted)
- World Builder: PASSED (10 world context fields, all entities described)
- World Config saved: test_project/world_bible/world_config.json

---

[DATE] 2026-01-14 - API Configuration & Model Registry

🔴 ➕🔧 🔧 .env 「API keys configured (xAI, Google, Replicate)」
└─ 🔗 CONFIG │ ◉🅐

🟠 📝✨ 📜 greenlight/core/config.py 「Added LLMModels, ImageModels classes, model aliases」
└─ 🔗 CONFIG │ ◉🅑

🟠 📝 📜 greenlight/core/isaac.py 「Updated to use ImageModels.ISAAC_01」
└─ 🔗 CONFIG │ ◉🅑

🟢 ➕📄 _CONTEXT/02_⚓_PROJECT_CONTEXT_IMMUTABLE/MODEL_REGISTRY.md 「Canonical model reference」
└─ 🔗 CONFIG │ ◉📍

🟢 📝📄 _CONTEXT/02_⚓_PROJECT_CONTEXT_IMMUTABLE/PROJECT_CONSTANTS.md 「Added API provider details」
└─ 🔗 CONFIG │ ◉📍

🟢 📝📄 _CONTEXT/02_⚓_PROJECT_CONTEXT_IMMUTABLE/TECH_STACK.md 「Updated with verified model identifiers」
└─ 🔗 CONFIG │ ◉📍

---

📅 2026-01-14 - Phase 2 Frontend Implementation

🔴 ➕✨ 🎨 web/src/components/modals/ingestion-modal.tsx 「File upload modal with drag & drop」
└─ 🔗 INGEST-002 │ ◉🅕

🔴 ➕✨ 🎨 web/src/components/modals/entity-confirmation-modal.tsx 「Entity review and confirmation UI」
└─ 🔗 INGEST-002 │ ◉🅕

🟠 📝✨ 🎨 web/src/components/modals/index.ts 「Added new modal exports」
└─ 🔗 INGEST-002 │ ◉🅕

🟠 📝✨ 🎨 web/src/components/header.tsx 「Added Ingest button and modal state」
└─ 🔗 INGEST-002 │ ◉🅕

---

📅 2026-01-14 - Phase 1 Implementation Session

🔴 ➕✨ 📜 greenlight/core/isaac.py 「Isaac 0.1 Replicate client for image analysis」
└─ 🔗 INGEST-001 │ ◉🅑

🔴 ➕✨ 📜 greenlight/core/ingestion.py 「Document/image ingestion pipeline with chunking」
└─ 🔗 INGEST-001 │ ◉🅑

🔴 ➕✨ 📡 greenlight/api/ingestion.py 「Ingestion API endpoints」
└─ 🔗 INGEST-001 │ ◉🅑

🔴 ➕✨ 📜 greenlight/pipelines/world_builder.py 「World bible builder with progressive fields」
└─ 🔗 INGEST-001 │ ◉🅑

🟠 📝✨ 📜 greenlight/core/models.py 「Added ingestion + world builder models」
└─ 🔗 INGEST-001 │ ◉🅑

🟠 📝✨ 📡 greenlight/api/main.py 「Added ingestion router」
└─ 🔗 INGEST-001 │ ◉🅑

🟠 📝✨ 📡 greenlight/api/pipelines.py 「Added world builder endpoint」
└─ 🔗 INGEST-001 │ ◉🅑

🟢 📝 📄 _CONTEXT/03_◆_CURRENT_STATE/STATE_SNAPSHOT.md 「Updated with Phase 1 completion」
└─ 🔗 INGEST-001 │ ◉📍

🟢 📝 📄 _OPERATIONS/TODO.md 「Updated task status」
└─ 🔗 INGEST-001 │ ◉📍

---

Example entries:

📅 2024-01-15

🟠 ➕✨ 📜 src/auth/login.js 「User login handler」
└─ 🔗 T-001 │ ◆🅑

🟡 📝🐛 🔧 src/utils/validate.js 「email regex fix」
└─ 🔗 T-002 │ ◉🅑

🟢 ➕📄 _CONTEXT/01_🎯_PRIMARY_GOAL/BOUNDARIES.md 「scope doc」
└─ 🔗 setup │ ◉🅐
```

---

## CHANGE TYPE REFERENCE

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

## FILE TYPE REFERENCE

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

---

## STATISTICS

```
TOTAL CHANGES: 19

By Type:
➕ Added: 8
📝 Modified: 11
➖ Removed: 0
🐛 Bugfixes: 0
✨ Features: 12

By Priority:
🔴 Critical: 7
🟠 High: 7
🟡 Medium: 0
🟢 Low: 5
```

---

DOCUMENT_STATUS: ◆_LIVE
TRACE: ◆📍
APPEND_ONLY: true
