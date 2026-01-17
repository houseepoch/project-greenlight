# TODO - Task Queue

> **Read at session start. Update after every task.**

---

## STATUS: ◉ ALL MAJOR TASKS COMPLETE

```
⏰ UPDATED: 2026-01-16 (Session 5)
📊 HEALTH: 🟢🟢🟢🟢🟢 (5/5)
📦 GITHUB: https://github.com/houseepoch/project-greenlight
```

---

## ◉ MOST RECENT COMPLETED

```
🟢 ICB-REMOVAL │ ◉🅑 │ 📅 01-16
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ICB Feature Removal + CORS Fixes

COMPLETED:
├─ ✅ CORS fixes for images/SSE (main.py, images.py, pipelines.py)
├─ ✅ ICB endpoints removed from pipelines.py
├─ ✅ greenlight/core/icb.py deleted
├─ ✅ ICB UI removed from storyboard-view.tsx
├─ ✅ ICB state/interfaces/functions cleaned up
├─ ✅ Frontend builds successfully
├─ ✅ Backend compiles without errors
└─ ✅ /sync-context complete

REASON: ICB results were bad - feature removed entirely
```

```
🟢 INGEST-002 │ ◉🅑 │ 📅 01-15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ingestion Refactor - Full Context + Consensus

COMPLETED:
├─ ✅ Removed chunking - full text processing
├─ ✅ 3-way consensus extraction (entities in ALL 3 calls)
├─ ✅ source_text.json saved for world builder
├─ ✅ Character-specific context extraction (4000 chars)
├─ ✅ Entity-specific context extraction (3000 chars)
├─ ✅ Full story context for world context (8000 chars)
├─ ✅ Tested: 7 chars, 9 locs, 2 props - all distinct
├─ ✅ Commit: 87e33ff
└─ ✅ /sync-context complete
```

```
🟢 IMGFIX-001 │ ◉🅑 │ 📅 01-15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Image Generation + UI Fixes

COMPLETED:
├─ ✅ Removed reference modal → Simple generate button
├─ ✅ Default model: p_image_edit → flux_2_pro
├─ ✅ Added MEDIA_TYPE_STYLES templates (no artists)
├─ ✅ Fixed Replicate auth (pydantic → os.environ)
├─ ✅ Fixed FileOutput handling (replicate library)
├─ ✅ Downgraded Tailwind 4 → 3 (compatibility)
├─ ✅ Pushed to GitHub
└─ ✅ /sync-context complete
```

```
🟢 GAPS-001 │ ◉🅑 │ 📅 01-15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline Gap Analysis + API Fixes

COMPLETED:
├─ ✅ Director pipeline rewritten (250-350 word prompts)
├─ ✅ References pipeline simplified (single image/entity)
├─ ✅ Storyboard pipeline (scene/frame granularity)
├─ ✅ Scene-by-scene storyboard API endpoint
├─ ✅ Frame regeneration API endpoint
├─ ✅ Prompt editing endpoints (GET/PUT)
├─ ✅ Reference image management (list/regenerate/delete)
├─ ✅ Pipeline validation endpoint
├─ ✅ Updated __init__.py with all exports
└─ ✅ 12/12 API tests passing
```

---

## ◇ QUEUE (Optional Polish)

```
🟡 UI-001 │ ◇🅕 │ Prompt Editor UI (use new /prompts endpoints)
🟡 UI-002 │ ◇🅕 │ Reference Manager UI (use new /references endpoints)
🟢 UI-003 │ ◇🅕 │ Scene-by-Scene Generation UI
```

---

## ◈ BLOCKED

```
[None currently]
```

---

## ◉ COMPLETED

```
✅ BASE-001 │ ◉🅑 │ 📅 01-14 │ LLM client (Grok 4.1 Fast) ✓
✅ BASE-002 │ ◉🅑 │ 📅 01-14 │ Character/Location models ✓
✅ BASE-003 │ ◉🅑 │ 📅 01-14 │ World context extraction ✓
✅ BASE-004 │ ◉🅑 │ 📅 01-14 │ 3-way consensus extraction ✓
✅ BASE-005 │ ◉🅑 │ 📅 01-14 │ Entity enrichment ✓
✅ BASE-006 │ ◉🅑 │ 📅 01-14 │ Story outline generation ✓
✅ BASE-007 │ ◉🅑 │ 📅 01-14 │ Director pipeline (frames) ✓
✅ DOC-001 │ ◉📍 │ 📅 01-14 │ Canonical tagging rules ✓
✅ PLAN-001 │ ◉🅐 │ 📅 01-14 │ Ingestion architecture plan ✓
✅ INGEST-001 │ ◉🅑 │ 📅 01-14 │ Core Ingestion Infrastructure ✓
✅ INGEST-002 │ ◉🅕 │ 📅 01-14 │ Entity Confirmation Modal ✓
✅ OUTLINE-001 │ ◉🅑 │ 📅 01-14 │ Outline Generator (3 variants) ✓
✅ DIRECTOR-001 │ ◉🅑 │ 📅 01-15 │ Director Rewrite (250-350 word prompts) ✓
✅ REFS-001 │ ◉🅑 │ 📅 01-15 │ References Pipeline Simplified ✓
✅ STORYBOARD-001 │ ◉🅑 │ 📅 01-15 │ Storyboard Scene/Frame Control ✓
✅ GAPS-001 │ ◉🅑 │ 📅 01-15 │ API Gap Fixes (10+ endpoints) ✓
✅ TEST-001 │ ◉🅣 │ 📅 01-15 │ API Endpoint Tests (12/12 passing) ✓
✅ INGEST-002 │ ◉🅑 │ 📅 01-15 │ Ingestion refactor (full context + 3-way consensus) ✓
✅ ICB-REMOVAL │ ◉🅑 │ 📅 01-16 │ ICB feature removed (bad results) + CORS fixes ✓
```

---

## 📊 SUMMARY

```
🟡 3  │ 3 optional UI tasks queued
◆ 0  ◇ 3  ◈ 0  ◉ 18    │ by state
```

---

## IMPLEMENTATION PHASES

```
Phase 1: Core Ingestion Infrastructure ◉ COMPLETE
  └─ isaac.py, ingestion.py, models, API, world_builder.py

Phase 2: Entity Confirmation ◉ COMPLETE
  └─ ingestion-modal.tsx, entity-confirmation-modal.tsx

Phase 3: World Bible View ◉ ALREADY EXISTS
  └─ world-view.tsx with edit capability

Phase 4: Outline Generator ◉ COMPLETE
  └─ 3 narrative approaches, variant selection

Phase 5: Director Pipeline Rewrite ◉ COMPLETE
  └─ 250-350 word prompts, camera coverage rules

Phase 6: References Pipeline ◉ COMPLETE
  └─ Single image per entity, simplified

Phase 7: Storyboard Pipeline ◉ COMPLETE
  └─ Scene/frame granularity, reference ordering

Phase 8: API Gap Fixes ◉ COMPLETE
  └─ All endpoints, validation, 12/12 tests passing
```

---

## NEW API ENDPOINTS (01-15)

```
POST /api/pipelines/storyboard/scene/{n}     - Scene-by-scene generation
POST /api/pipelines/storyboard/frame/{id}    - Frame regeneration
GET  /api/pipelines/prompts/{path}           - Get prompts for editing
PUT  /api/pipelines/prompts/{path}           - Save edited prompts
PUT  /api/pipelines/prompts/{path}/frame/{id} - Update single prompt
GET  /api/pipelines/references/{path}        - List reference images
POST /api/pipelines/references/{path}/regenerate/{tag} - Regenerate one
DELETE /api/pipelines/references/{path}/{tag} - Delete reference
GET  /api/pipelines/validate/{path}          - Check pipeline readiness
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

TRACE: ●◉GAPS-001
