# Glossary (Immutable)

> **Canonical terms used in this project.**
> **Use these exact terms for consistency.**

---

## DOMAIN TERMS

| Term | Definition | Context |
|------|------------|---------|
| Pitch | Initial story idea/treatment (legacy input method) | Optional, replaced by ingestion |
| Ingestion | Multi-document/image upload and processing | New primary input method |
| Chunk | Fixed-size text segment (500-1000 tokens) | Document processing |
| World Context | Setting details (time period, culture, clothing) | Rolls over to all entities |
| Entity | Any tagged item: character, location, or prop | Used throughout pipelines |
| Entity Confirmation | User review of extracted entities before world building | Modal workflow |
| World Bible | Complete world configuration with all fields | Project foundation |
| Story Outline | Light, editable scene breakdown (events/beats) | User review before Director |
| Visual Script | Frame-by-frame shot breakdown with prose | Director pipeline output |
| Frame | Single shot with prompt, prose, and metadata | Image generation unit |
| Reference Image | Visual reference for an entity | On-demand generation or upload |

---

## TECHNICAL TERMS

| Term | Definition | Context |
|------|------------|---------|
| Tag | Unique identifier for entities (CHAR_NAME, LOC_NAME, PROP_NAME) | All entity references |
| World Config | Complete world bible JSON (world_config.json) | Contains all world data |
| Beat | Key moment within a scene | Story outline structure |
| Camera Notation | Shot type abbreviation (WS, MS, CU, ECU, OTS) | Frame metadata |
| Location Direction | Cardinal direction for camera reference (N/E/S/W) | Location views |
| Token | Unit of text for LLM processing | Chunking measurement |
| Overlap | Shared tokens between adjacent chunks (10%) | Context preservation |
| Progressive Population | Fields update in real-time as LLM completes | World builder pattern |

---

## INGESTION TERMS

| Term | Definition | Context |
|------|------------|---------|
| Isaac 0.1 | Vision-language model for image analysis | Via Replicate API |
| Document Processing | Text extraction from PDF, DOCX, MD, TXT | Ingestion pipeline |
| Image Analysis | Isaac-powered scene/entity extraction from images | Ingestion pipeline |
| Session | Active ingestion workflow with status tracking | API state management |
| Extracted Entity | Pre-confirmation entity with suggested type | Before user review |
| Confirmed Entity | Entity with user-assigned type | After user review |

---

## ABBREVIATIONS

| Abbrev | Full Term | Usage |
|--------|-----------|-------|
| WS | Wide Shot | Camera notation |
| MS | Medium Shot | Camera notation |
| CU | Close-Up | Camera notation |
| ECU | Extreme Close-Up | Camera notation |
| OTS | Over The Shoulder | Camera notation |
| N/E/S/W | North/East/South/West | Location direction |

---

## NAMING CONVENTIONS

### Files
```
- Components: PascalCase.tsx
- Utilities: camelCase.ts
- Tests: *.test.ts
- Pipeline outputs: snake_case.json
- Uploaded docs: original_filename.ext
```

### Variables
```
- Constants: UPPER_SNAKE_CASE
- Functions: camelCase
- Classes: PascalCase
```

### Database
```
- Tables: snake_case
- Columns: snake_case
```

---

## CANONICAL TAGGING RULES ⚓

### Tag Format
```
PREFIX_NAME_DESCRIPTOR
```

**CRITICAL:** All tags must follow these rules exactly.

### Entity Prefixes

| Prefix | Entity Type | Example |
|--------|-------------|---------|
| `CHAR_` | Character | `CHAR_MEI`, `CHAR_WANG`, `CHAR_OLD_POET` |
| `LOC_` | Location | `LOC_PALACE`, `LOC_MEI_BEDROOM`, `LOC_COURTYARD` |
| `PROP_` | Prop | `PROP_SWORD`, `PROP_JADE_PIN`, `PROP_SCROLL` |

### Naming Rules

1. **UPPERCASE_WITH_UNDERSCORES**
   - ✅ `CHAR_MEI_LING`
   - ❌ `CHAR_MeiLing`
   - ❌ `char_mei_ling`

2. **Use descriptive names**
   - ✅ `LOC_PALACE_GARDEN`
   - ❌ `LOC_GARDEN1`
   - ❌ `LOC_G`

3. **Avoid generic tags**
   - ✅ `CHAR_OLD_POET`
   - ❌ `CHAR_MAN`
   - ❌ `CHAR_PERSON`

4. **No placeholders**
   - ❌ `[CHARACTER_NAME]`
   - ❌ `[LOCATION]`
   - ❌ `CHAR_TBD`

### Tag Usage

- Tags are case-sensitive: `CHAR_MEI` ≠ `char_mei`
- Tags must be unique per entity type
- Tags persist across all pipelines
- Tags appear in:
  - `world_config.json` (entity definitions)
  - `story_outline.json` (scene assignments)
  - `visual_script.json` (frame references)
  - `prompts.json` (image generation)

### Examples by Entity Type

**Characters:**
```
CHAR_MEI           - Main character "Mei"
CHAR_WANG_JUN      - Character "Wang Jun"
CHAR_MADAM_LI      - Character "Madam Li"
CHAR_PALACE_GUARD  - Generic role with descriptor
```

**Locations:**
```
LOC_BROTHEL_MAIN_HALL    - Specific room
LOC_MEI_BEDROOM          - Character-specific location
LOC_PALACE_COURTYARD     - Location within location
LOC_RIVER_DOCK           - Outdoor location
```

**Props:**
```
PROP_JADE_HAIRPIN    - Specific named prop
PROP_POETRY_SCROLL   - Descriptive prop
PROP_DAGGER          - Simple prop
PROP_WINE_CUP        - Common prop
```

---

## FIELD LENGTH RULES ⚓

| Field Type | Word Count | Example |
|------------|------------|---------|
| All world bible fields | 10-24 words | Concise, scannable descriptions |
| Character appearance | 10-24 words | Physical features, age, build |
| Character clothing | 10-24 words | Period-appropriate attire |
| Location description | 10-24 words | Key visual elements |
| Prop description | 10-24 words | Appearance and significance |

---

## PIPELINE STATUS VALUES

| Status | Meaning | Context |
|--------|---------|---------|
| `pending` | Not started | Field/task waiting |
| `generating` | LLM processing | Field being created |
| `complete` | Done | Field ready for use |
| `edited` | User modified | Field changed by user |
| `draft` | Awaiting confirmation | Story outline |
| `confirmed` | User approved | Ready for next pipeline |
| `uploading` | Files being uploaded | Ingestion session |
| `processing` | Documents being processed | Ingestion session |
| `extracting` | Entities being extracted | Ingestion session |
| `confirming` | Awaiting user confirmation | Ingestion session |
| `building` | World bible in progress | World builder |

---

## FORBIDDEN TERMS

| Don't Use | Use Instead | Reason |
|-----------|-------------|--------|
| `[PLACEHOLDER]` | Actual tag | No placeholders in tags |
| `char_name` | `CHAR_NAME` | Must be uppercase |
| `CHARACTER_1` | `CHAR_DESCRIPTIVE` | No generic numbering |
| Mixed case | `UPPER_SNAKE_CASE` | Consistency required |
| `script.md` | `story_outline.json` | Legacy term |
| `pitch-only` | `ingestion` | New primary method |

---

DOCUMENT_STATUS: ⚓_IMMUTABLE
TRACE: ●⚓📍
