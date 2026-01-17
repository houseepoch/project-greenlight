# State Snapshot

> **Current state of the project. Updated frequently.**

---

## CURRENT STATUS

```
UPDATED: 2026-01-16 (Session 5)
PHASE: ICB Removed, CORS Fixes Applied
ACTIVE TASK: Ready for Production Testing
MODE: DEFAULT
API STATUS: All keys configured [OK]
GITHUB: https://github.com/houseepoch/project-greenlight
```

---

## PROJECT HEALTH

```
Goal alignment: OK
Progress: 98% (Full Pipeline + Storyboard Reference Integration)
Blockers: 0
Completed: 25 (All phases + Reference image wiring + Model selection)
Queued: Production testing only
```

---

## RECENT ACTIVITY

### Current Session (Part 5)
```
Date: 2026-01-16
Duration: ICB Feature + CORS Fixes + ICB Removal

CORS FIXES:
   - Added expose_headers=["*"] to CORS middleware (main.py)
   - Added Access-Control-Allow-Origin: * to images.py FileResponse
   - Added explicit CORS headers to SSE StreamingResponse in pipelines.py
   - Images now load correctly from localhost:3000 → localhost:8000

ICB (INTELLIGENT CONTINUITY BLENDING) - REMOVED:
   - Feature was added to fix continuity issues on storyboard frames
   - Used AI image editing to apply targeted fixes per issue
   - Job state persistence for resume/reset capability
   - SSE streaming for real-time progress updates
   - RESULTS WERE BAD - feature removed entirely
   - Removed from: pipelines.py, icb.py (deleted), storyboard-view.tsx
```

### Session 4
```
Date: 2026-01-15
Duration: Ingestion Refactor - Full Context + Consensus

INGESTION PIPELINE REFACTOR:
   - Removed chunking entirely - process full pitch as single unit
   - 3-way consensus extraction (entities must appear in ALL 3 parallel LLM calls)
   - Saves source_text.json for world builder (not chunks.json)
   - Full story context preserved for accurate entity descriptions

WORLD BUILDER UPDATES:
   - Character-specific context extraction (up to 4000 chars per character)
   - Entity-specific context extraction (up to 3000 chars for locations/props)
   - Uses full story context (8000 chars) for world context generation
   - Distinct, accurate character descriptions based on actual story content

TESTING:
   - Tested with multi-chapter script (7 characters, 9 locations, 2 props)
   - Character descriptions now distinct and story-accurate
   - World context properly reflects setting (near-future Hokkaido, Japan)
   - Commit: 87e33ff
```

### Session 3
```
Date: 2026-01-15
Duration: Storyboard Reference Image Integration

STORYBOARD REFERENCE INTEGRATION:
   - Fixed Replicate API parameters:
     * Flux 2 Pro: reference_images → input_images
     * Seedream 4.5: uses image_input parameter
     * Model IDs updated to latest versions
   - Safety tolerance set to 5 (most permissive) for Flux models
   - Reference image labeling: yellow text with black outline overlay
   - Entity lookup enhanced with spelling variations (partial matching)

MODEL SELECTION UI:
   - Added /api/settings/storyboard-models endpoint
   - Storyboard modal dropdown: Flux 2 Pro (default), Seedream 4.5, Nano Banana Pro
   - Removed deprecated Flux 1.1 Pro and Z Image models

TESTING:
   - Generated 8 frames across 3 scenes with reference images
   - Verified character consistency with reference images
   - Compared Flux 2 Pro vs Seedream 4.5 (Seedream better likeness)
```

### Session 2
```
Date: 2026-01-15
Duration: Image Generation Fixes + UI Polish

IMAGE GENERATION FIXES:
   - Removed reference modal → Simple "Generate" button on entity cards
   - Default model changed: p_image_edit → flux_2_pro
   - Added media type style templates (MEDIA_TYPE_STYLES dict)
   - Fixed Replicate auth: pydantic settings → os.environ export
   - Fixed FileOutput handling (replicate library update)
   - Downgraded Tailwind 4 → Tailwind 3 (compatibility)

GIT:
   - Initialized repo, pushed to GitHub
   - https://github.com/houseepoch/project-greenlight
```

### Session 1
```
Date: 2026-01-15
Duration: Director Rewrite + Gap Analysis + API Fixes

DIRECTOR PIPELINE REWRITE:
   - Rewrote director.py to read from confirmed_outline.json
   - Frame prompts now 250-350 words (cinematic, self-contained)
   - Camera coverage rules: dialogue needs speaker + listener reaction
   - Frame ID format: {scene}.{frame}.c{camera} (e.g., "1.1.cA")
   - Tags are metadata only (prompts use character names)
   - Test PASSED: 10 frames across 3 scenes, 227-295 words each

REFERENCES PIPELINE SIMPLIFIED:
   - Single image per entity (not multi-angle sheets)
   - Templates: CHARACTER_REF_PROMPT, LOCATION_REF_PROMPT, PROP_REF_PROMPT
   - Reference naming: {TAG}.png (e.g., CHAR_MEI.png)

STORYBOARD PIPELINE UPDATED:
   - Reference image ordering: Location → Characters → Props → Prior frame
   - Scene-by-scene generation option (scene_filter parameter)
   - Single frame regeneration (generate_single_frame())
   - Convenience functions: generate_storyboard(), generate_scene(), generate_frame()

GAP ANALYSIS + FIXES (12 tests passed):
   - Added scene-by-scene storyboard endpoint: POST /storyboard/scene/{n}
   - Added frame regeneration endpoint: POST /storyboard/frame/{id}
   - Added prompt editing endpoints: GET/PUT /prompts/{path}
   - Added reference management: GET/POST/DELETE /references/{path}
   - Added pipeline validation: GET /validate/{path}
   - Updated PipelineRequest with scene_filter, entity_filter
   - Updated pipelines __init__.py with all exports
   - All 12 API endpoint tests PASSED
```

---

## NEW ARCHITECTURE

```
Documents/Images Upload
(.zip, .png, .jpg, .txt, .md, .pdf, .docx)
    │
    ▼
┌─────────────────────────────────────────────┐
|           INGESTION PIPELINE                | [OK] COMPLETE
├─────────────────────────────────────────────┤
│ [1] Process pitch/synopsis text             │
│ [2] Full context processing (no chunking)   │
│ [3] 3-way consensus entity extraction       │
│     - 3 parallel LLM calls                  │
│     - Only entities in ALL 3 are kept       │
│ [4] Save source_text.json for world builder │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
|       ENTITY CONFIRMATION MODAL [PAUSE]     | [OK] COMPLETE
│  - Review extracted entity names            │
│  - User assigns type (CHAR_/LOC_/PROP_)     │
│  - Add/remove entities                      │
│  - Confirm launches world builder           │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
|         WORLD BIBLE BUILDER                 | [OK] COMPLETE
├─────────────────────────────────────────────┤
│ [1] Initialize fields (all pending)         │
│ [2] Generate core fields (parallel)         │
│     - setting, time_period, tone, style     │
│ [3] Generate entity descriptions            │
│     - Characters: appearance, clothing...   │
│     - Locations: description, N/E/S/W       │
│     - Props: description, significance      │
│ [4] Fields populate progressively           │
│     (10-24 words each)                      │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
|         WORLD BIBLE PAGE [PAUSE]            | [OK] EXISTS
│  - View/edit fields as they complete        │
│  - Reference images: on-demand generation   │
│  - Upload replaces AI-generated reference   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
|         WRITER PIPELINE                     | [OK] EXISTS
│         (Fast Outline Only)                 │
├─────────────────────────────────────────────┤
│ - Input: world_config.json                  │
│ - Output: story_outline.json                │
│ - Events/beats for user to confirm/edit     │
└─────────────────────────────────────────────┘
    │
    ▼
USER CONFIRMS OUTLINE [PAUSE]
    │
    ▼
┌─────────────────────────────────────────────┐
|         DIRECTOR PIPELINE                   | [OK] EXISTS
│         (Full Prose + Frames)               │
├─────────────────────────────────────────────┤
│ [1] Full prose scene writing                │
│     - Dialogue, action, emotion             │
│ [2] Frame-by-frame breakdown                │
│ [3] Image prompt per frame                  │
│     - Detailed, cinematic prompts           │
└─────────────────────────────────────────────┘
    │
    ▼
OUTPUT: visual_script.json + prompts.json
```

---

## KEY FILES

### Backend
| File | Purpose | Status |
|------|---------|--------|
| `greenlight/core/config.py` | Settings + Model Registry | [OK] Done |
| `greenlight/core/llm.py` | Grok 4.1 Fast client | [OK] Done |
| `greenlight/core/models.py` | Data models + ingestion models | [OK] Done |
| `greenlight/core/isaac.py` | Isaac 0.1 client (Replicate) | [OK] Done |
| `greenlight/core/ingestion.py` | Doc processing, chunking, extraction | [OK] Done |
| `greenlight/api/ingestion.py` | Ingestion API endpoints | [OK] Done |
| `greenlight/api/pipelines.py` | Pipeline endpoints + world builder | [OK] Done |
| `greenlight/pipelines/world_builder.py` | World bible builder | [OK] Done |
| `greenlight/pipelines/writer.py` | Outline generator | [OK] Done |
| `greenlight/pipelines/director.py` | Prose + frames | [OK] Done |
| `.env` | API keys (configured) | [OK] Done |

### Frontend
| File | Purpose | Status |
|------|---------|--------|
| `web/src/components/modals/ingestion-modal.tsx` | File upload UI | [OK] Done |
| `web/src/components/modals/entity-confirmation-modal.tsx` | Entity review UI | [OK] Done |
| `web/src/components/header.tsx` | Added Ingest button | [OK] Done |
| `web/src/components/views/world-view.tsx` | World bible display | [OK] Exists |

---

## API ENDPOINTS

### Ingestion API (`/api/ingestion`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upload` | POST | Upload files to project |
| `/start` | POST | Start ingestion pipeline |
| `/status/{id}` | GET | Get pipeline status |
| `/entities/{path}` | GET | Get extracted entities |
| `/confirm-entities` | POST | Confirm entity selections |
| `/add-entity` | POST | Manually add entity |
| `/remove-entity` | DELETE | Remove entity |
| `/chunks/{path}` | GET | Get processed chunks |

### Pipelines API (`/api/pipelines`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/world-builder` | POST | Start world builder pipeline |
| `/writer` | POST | Start writer pipeline |
| `/director` | POST | Start director pipeline |
| `/references` | POST | Start references pipeline |
| `/storyboard` | POST | Start storyboard pipeline |
| `/storyboard/scene/{n}` | POST | Generate single scene |
| `/storyboard/frame/{id}` | POST | Regenerate single frame |
| `/prompts/{path}` | GET/PUT | Get/save frame prompts |
| `/references/{path}` | GET | List reference images |
| `/references/{path}/regenerate/{tag}` | POST | Regenerate single reference |
| `/references/{path}/{tag}` | DELETE | Delete reference image |
| `/validate/{path}` | GET | Check pipeline readiness |

---

## IMPLEMENTATION PHASES

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Core Ingestion Infrastructure (Backend) | [OK] Complete |
| 2 | Entity Confirmation (Frontend Modal) | [OK] Complete |
| 3 | World Bible View (Already Exists) | [OK] Complete |
| 4 | Integration Testing | [OK] Complete |
| 5 | Director Pipeline Rewrite | [OK] Complete |
| 6 | References Pipeline Simplified | [OK] Complete |
| 7 | Storyboard Pipeline Updated | [OK] Complete |
| 8 | API Gap Fixes | [OK] Complete |
| 9 | Storyboard Reference Integration | [OK] Complete |
| 10 | Model Selection UI | [OK] Complete |

---

## USER FLOW

```
1. User clicks "Ingest" button in header
2. Ingestion Modal opens
   - Drag & drop files (PDF, DOCX, TXT, MD, images, ZIP)
   - Click "Start Ingestion"
   - Watch progress as files are processed
3. On completion, Entity Confirmation Modal opens
   - Review extracted characters, locations, props
   - Assign/edit canonical tags (CHAR_*, LOC_*, PROP_*)
   - Add missing entities manually
   - Remove false positives
4. Click "Build World Bible"
   - World Builder pipeline runs
   - Progress shown in Progress view
5. World Bible page shows results
   - Edit fields as needed
   - Generate reference images on-demand
```

---

## USER PREFERENCES ⚓

```
Ingestion:       Full context (no chunking), 3-way consensus extraction
Entity types:    User assigns type in modal (with suggestions)
Reference timing: On-demand generation
Upload behavior:  Replace (upload replaces AI generation)
```

---

## CANONICAL TAGS

```
CHAR_   Characters (CHAR_MEI, CHAR_WANG)
LOC_    Locations  (LOC_PALACE, LOC_BEDROOM)
PROP_   Props      (PROP_SWORD, PROP_SCROLL)

Format: PREFIX_UPPER_SNAKE_CASE
```

---

## STORYBOARD IMAGE MODELS

| Model | Provider | Max Refs | Best For |
|-------|----------|----------|----------|
| Flux 2 Pro (default) | Replicate | 8 | High quality, character consistency |
| Seedream 4.5 | Replicate | 14 | Fast, excellent likeness preservation |
| Nano Banana Pro | Gemini | 4 | Fast generation, good quality |

### API Parameters
```
Flux 2 Pro:
   - Parameter: input_images (not reference_images)
   - safety_tolerance: 5 (most permissive)
   - output_format: png

Seedream 4.5:
   - Parameter: image_input
   - Up to 14 reference images

Nano Banana Pro:
   - Uses Gemini API with inline_data
   - Up to 4 reference images
```

---

DOCUMENT_STATUS: ◆_LIVE
TRACE: ◆📍🅑🅕
AUTO_UPDATED: true
