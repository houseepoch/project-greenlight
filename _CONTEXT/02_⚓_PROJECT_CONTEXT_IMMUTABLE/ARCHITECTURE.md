# Architecture (Immutable)

> **System design and architectural decisions.**
> **Only modify via `/set-project-context` command.**

---

## SYSTEM OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PROJECT GREENLIGHT                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               │
│   │   Next.js   │────▶│   FastAPI   │────▶│   Grok 4.1  │               │
│   │   Frontend  │◀────│   Backend   │◀────│   Fast API  │               │
│   └─────────────┘     └─────────────┘     └─────────────┘               │
│         │                   │                    │                       │
│         │                   │              ┌─────────────┐               │
│         │                   │              │  Isaac 0.1  │               │
│         │                   │              │  (Replicate)│               │
│         │                   │              └─────────────┘               │
│         │                   ▼                                            │
│         │           ┌─────────────┐                                      │
│         │           │  Pipelines  │                                      │
│         │           │  Ingestion  │ ← NEW                                │
│         │           │  WorldBuilder│ ← NEW                               │
│         │           │  Writer     │ ← Refactored                         │
│         │           │  Director   │ ← Refactored                         │
│         │           │  References │                                      │
│         │           │  Storyboard │                                      │
│         │           └─────────────┘                                      │
│         │                   │                                            │
│         ▼                   ▼                                            │
│   ┌─────────────────────────────────────┐                                │
│   │           File System                │                                │
│   │  uploads/ world_bible/ storyboard/   │                                │
│   └─────────────────────────────────────┘                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## COMPLETE PIPELINE FLOW ⚓

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DOCUMENT/IMAGE INGESTION                             │
│                     (NEW - Replaces Pitch-Only)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SUPPORTED INPUTS:                                                       │
│  .zip, .png, .jpeg, .jpg, .txt, .md, .pdf, .docx                        │
│                                                                          │
│  [1] FILE EXTRACTION                                                     │
│      - Unzip if .zip                                                     │
│      - Validate file types                                               │
│      - Generate content hashes                                           │
│                                                                          │
│  [2] DOCUMENT PROCESSING                                                 │
│      - Text/MD: Direct read                                              │
│      - PDF: pypdf text extraction                                        │
│      - DOCX: python-docx text extraction                                 │
│      - Images: Isaac 0.1 via Replicate                                   │
│        └─ Returns: description, entities, scene_type                     │
│                                                                          │
│  [3] CHUNKING                                                            │
│      - Fixed token chunks (500-1000 tokens)                              │
│      - 10% overlap between chunks                                        │
│      - Token counting via tiktoken                                       │
│      - Chunk metadata preserved                                          │
│                                                                          │
│  [4] ENTITY EXTRACTION                                                   │
│      - LLM analysis of all chunks                                        │
│      - Extract entity names                                              │
│      - Suggest entity types (CHAR_/LOC_/PROP_)                          │
│      - Confidence scoring                                                │
│      - Deduplication across chunks                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENTITY CONFIRMATION MODAL ⏸                           │
│                    (User Review Point)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  USER ACTIONS:                                                           │
│  - Review extracted entity names                                         │
│  - Assign type per entity (Character / Location / Prop / Remove)        │
│  - Add new entities manually                                             │
│  - Remove false positives                                                │
│  - Confirm to launch World Builder                                       │
│                                                                          │
│  OUTPUT: Confirmed entity list with user-assigned types                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       WORLD BIBLE BUILDER                                │
│                       (Progressive Population)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [1] INITIALIZE FIELDS                                                   │
│      - Create all world bible fields (pending status)                    │
│      - Categories: general, characters, locations, props, themes         │
│                                                                          │
│  [2] GENERATE CORE FIELDS (parallel)                                     │
│      - setting_overview (10-24 words)                                    │
│      - time_period (10-24 words)                                         │
│      - tone_mood (10-24 words)                                           │
│      - visual_style (10-24 words)                                        │
│                                                                          │
│  [3] GENERATE ENTITY FIELDS (parallel per entity)                        │
│      Characters:                                                         │
│        - appearance (10-24 words)                                        │
│        - clothing (10-24 words)                                          │
│        - personality (10-24 words)                                       │
│        - summary (10-24 words)                                           │
│      Locations:                                                          │
│        - description (10-24 words)                                       │
│        - atmosphere (10-24 words)                                        │
│        - view_north/east/south/west                                      │
│      Props:                                                              │
│        - description (10-24 words)                                       │
│        - significance (10-24 words)                                      │
│                                                                          │
│  [4] PROGRESSIVE UPDATES                                                 │
│      - Fields update in real-time as LLM completes                       │
│      - Status per field: pending → generating → complete                 │
│      - Frontend polls for updates                                        │
│                                                                          │
│  OUTPUT: world_config.json (populated progressively)                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       WORLD BIBLE PAGE ⏸                                 │
│                       (User Edit Point)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  USER ACTIONS:                                                           │
│  - View fields as they populate                                          │
│  - Edit any field inline                                                 │
│  - Regenerate individual fields                                          │
│  - Generate reference images (on-demand)                                 │
│  - Upload images to replace AI references                                │
│  - Proceed to Writer when satisfied                                      │
│                                                                          │
│  REFERENCE IMAGES:                                                       │
│  - On-demand generation (user clicks per entity)                         │
│  - Upload replaces AI-generated reference                                │
│  - Old references archived to _archive/                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       WRITER PIPELINE                                    │
│                       (Fast Outline Only)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INPUT: world_config.json (confirmed entities + world context)           │
│                                                                          │
│  PROCESS:                                                                │
│  - Generate story outline (events/beats)                                 │
│  - Scene-by-scene structure                                              │
│  - Character assignments per scene                                       │
│  - Location assignments per scene                                        │
│  - Fast, light descriptions                                              │
│                                                                          │
│  OUTPUT: story_outline.json (status: "draft")                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    USER CONFIRMS/EDITS OUTLINE ⏸                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (status: "confirmed")
┌─────────────────────────────────────────────────────────────────────────┐
│                       DIRECTOR PIPELINE                                  │
│                       (Full Prose + Frames + Prompts)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INPUT: story_outline.json (confirmed) + world_config.json               │
│                                                                          │
│  [1] FULL PROSE SCENE WRITING                                            │
│      - Complete prose for each scene                                     │
│      - Dialogue, action, emotion                                         │
│      - World context informs all descriptions                            │
│                                                                          │
│  [2] FRAME-BY-FRAME BREAKDOWN                                            │
│      - 3-6 frames per scene                                              │
│      - Camera notation (WS, MS, CU, ECU, OTS)                           │
│      - Location direction (N/E/S/W)                                      │
│      - Entity tags per frame                                             │
│                                                                          │
│  [3] IMAGE PROMPT GENERATION                                             │
│      - One detailed prompt per frame                                     │
│      - Cinematic, specific descriptions                                  │
│      - Character clothing/appearance injected                            │
│      - Location atmosphere injected                                      │
│                                                                          │
│  OUTPUT:                                                                 │
│  - visual_script.json (prose + frames + prompts)                         │
│  - prompts.json (editable prompts for image generation)                  │
│  - visual_script.md (readable version)                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STORYBOARD PIPELINE                                   │
│                    (Image Generation)                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  - Generate images from prompts                                          │
│  - Reference images used for consistency                                 │
│  - Frame-by-frame output                                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ARCHITECTURAL PATTERNS

| Pattern | Description | Where Used |
|---------|-------------|------------|
| Document Ingestion | Multi-format file processing | Ingestion pipeline |
| Isaac Vision Analysis | Image understanding via Replicate | Image processing |
| Fixed Token Chunking | Consistent chunk sizes with overlap | Text processing |
| Entity Confirmation | User review before world building | Entity modal |
| Progressive Population | Fields update as LLM completes | World builder |
| On-Demand References | User-triggered image generation | Reference images |
| Upload-to-Replace | User uploads override AI references | Reference images |
| Canonical Tagging | Consistent CHAR_/LOC_/PROP_ prefixes | All entities |
| JSON-First Output | Structured data for editability | All pipeline outputs |

---

## DATA FLOW

```
User Upload (documents/images)
    │
    ▼
File Extraction + Type Validation
    │
    ▼
Document Processing
    │
    ├── Text/MD: Direct read
    ├── PDF: pypdf extraction
    ├── DOCX: python-docx extraction
    └── Images: Isaac 0.1 analysis
    │
    ▼
Chunking (500-1000 tokens, 10% overlap)
    │
    ▼
Entity Extraction from Chunks
    │
    ▼
USER REVIEW: Entity Confirmation ⏸
    │
    ▼
World Bible Building (progressive)
    │
    ├── Core fields (setting, time, tone, style)
    ├── Characters (appearance, clothing, personality)
    ├── Locations (description, N/E/S/W views)
    └── Props (description, significance)
    │
    ▼
USER EDIT: World Bible Page ⏸
    │
    ▼
Writer Pipeline (fast outline)
    │
    ▼
USER CONFIRM: Story Outline ⏸
    │
    ▼
Director Pipeline (prose + frames + prompts)
    │
    ▼
Visual Script + Image Prompts
```

---

## KEY DECISIONS ⚓

| Decision | Choice | Rationale | Locked |
|----------|--------|-----------|--------|
| LLM Provider | Grok 4.1 Fast only | Speed, simplicity, cost | ⚓ |
| Vision Model | Isaac 0.1 via Replicate | Best-in-class image analysis | ⚓ |
| Chunking | Fixed tokens (500-1000) | Consistent, predictable | ⚓ |
| Overlap | 10% token overlap | Context preservation | ⚓ |
| Entity Types | User assigns in modal | Accuracy over automation | ⚓ |
| Field Length | 10-24 words per field | Concise, scannable | ⚓ |
| Reference Timing | On-demand generation | User control, cost savings | ⚓ |
| Upload Behavior | Replace AI reference | Clear ownership | ⚓ |
| Tag Format | PREFIX_UPPER_SNAKE | Consistency across pipeline | ⚓ |

---

## FILE STRUCTURE

```
project_path/
├── project.json               # Project metadata
├── uploads/                   # Uploaded source documents
│   ├── documents/             # Text, PDF, DOCX files
│   └── images/                # Source images
├── ingestion/                 # Ingestion artifacts
│   ├── chunks.json            # Processed chunks
│   └── extracted_entities.json # Pre-confirmation entities
├── world_bible/
│   ├── pitch.md               # Legacy (optional)
│   └── world_config.json      # World context + entities
├── story_outline.json         # Editable scene breakdown
├── storyboard/
│   ├── visual_script.json     # Prose + frames + prompts
│   ├── visual_script.md       # Human-readable version
│   └── prompts.json           # Editable image prompts
├── references/                # Entity reference images
│   ├── _archive/              # Replaced references
│   └── CHAR_NAME.png          # Current references
└── storyboard_output/
    └── generated/             # Final storyboard images
```

---

## API STRUCTURE

### Ingestion Router (`/api/ingestion/`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/upload` | Upload files (multipart, zip support) |
| GET | `/status/{session_id}` | Get ingestion status |
| POST | `/extract-entities` | Run entity extraction |
| GET | `/entities/{session_id}` | Get entities for confirmation |
| POST | `/confirm-entities` | Submit confirmed entities |
| POST | `/cancel/{session_id}` | Cancel session |

### Projects Router (`/api/projects/`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/{name}/world-bible` | Get world bible with fields |
| PATCH | `/{name}/world-bible/field/{key}` | Update single field |
| POST | `/{name}/world-bible/regenerate/{key}` | Regenerate field |
| POST | `/{name}/references/{tag}/upload` | Upload replacement reference |

### Pipelines Router (`/api/pipelines/`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/world-builder` | Run world builder |
| POST | `/writer` | Run writer (outline) |
| POST | `/director` | Run director (prose + frames) |
| GET | `/status/{pipeline_id}` | Get pipeline status |

---

## CONSTRAINTS

### Technical Constraints
```
- Single LLM provider (Grok 4.1 Fast via xAI API)
- Vision model via Replicate (Isaac 0.1)
- No database (file-based storage)
- Async-first Python backend
- Next.js React frontend with Zustand state
```

### Scaling Considerations
```
- Parallel LLM calls for field generation
- Chunked processing for large documents
- Progressive updates to reduce perceived latency
- On-demand reference generation for cost control
```

---

DOCUMENT_STATUS: ⚓_IMMUTABLE
TRACE: ●⚓🅐📍
