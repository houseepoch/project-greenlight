# 🎯 Primary Goal Definition

> **This defines WHAT we're building and WHY.**
> All decisions must align with this document.

---

## THE GOAL

### What Are We Building?
```
Project Greenlight: AI-powered cinematic storyboard generator

A pipeline system that transforms source documents and images into
complete visual storyboards with:
- Multi-format document/image ingestion
- Entity extraction with user confirmation
- Progressive world bible generation
- Story outline creation
- Full prose scene writing
- Frame-by-frame image prompts
- Reference image generation/management
```

### Why Does This Exist?
```
To dramatically accelerate the pre-production process for
filmmakers, animators, and content creators by:
- Automating entity extraction from source materials
- Maintaining visual consistency through world bibles
- Generating production-ready storyboard frames
- Providing user control at every stage
```

### Who Is This For?
```
- Independent filmmakers planning productions
- Animation studios doing pre-visualization
- Content creators building visual narratives
- Writers wanting to visualize their stories
```

---

## OPERATIONAL FUNCTIONS

### User Interactions (Inputs)
```
INGESTION:
- Upload documents (.txt, .md, .pdf, .docx)
- Upload images (.png, .jpg, .jpeg)
- Upload archives (.zip with mixed content)

ENTITY CONFIRMATION:
- Review extracted entity names
- Assign types (Character / Location / Prop)
- Add new entities
- Remove false positives
- Confirm to launch world builder

WORLD BIBLE:
- View fields as they populate (10-24 words each)
- Edit any field inline
- Regenerate individual fields
- Generate reference images (on-demand)
- Upload images to replace AI references

STORY OUTLINE:
- Review generated scene outline
- Edit scenes and beats
- Confirm to launch Director

VISUAL SCRIPT:
- View prose scenes
- Review frame prompts
- Edit prompts before generation
```

### Desired Outputs
```
INGESTION OUTPUT:
- chunks.json (processed document chunks)
- extracted_entities.json (pre-confirmation entities)

WORLD BUILDER OUTPUT:
- world_config.json (complete world bible)
  - World context (setting, time, culture)
  - Characters (appearance, clothing, personality)
  - Locations (description, N/E/S/W views)
  - Props (description, significance)

WRITER OUTPUT:
- story_outline.json (scene-by-scene breakdown)

DIRECTOR OUTPUT:
- visual_script.json (prose + frames + prompts)
- visual_script.md (human-readable)
- prompts.json (editable image prompts)

REFERENCE OUTPUT:
- Entity reference images (on-demand)
- User-uploaded replacements

STORYBOARD OUTPUT:
- Generated frame images
```

### System Behaviors
```
INGESTION:
- Extract text from PDF, DOCX, TXT, MD
- Analyze images with Isaac 0.1 via Replicate
- Chunk text at 500-1000 tokens with 10% overlap
- Extract entities from chunks with LLM
- Deduplicate entities across chunks

WORLD BUILDER:
- Initialize all fields as pending
- Generate fields in parallel (10-24 words each)
- Update fields progressively as LLM completes
- Support individual field regeneration

WRITER:
- Generate fast story outline from world config
- Create scenes with beats, characters, locations
- Status: "draft" until user confirms

DIRECTOR:
- Require confirmed story outline
- Generate full prose per scene
- Create 3-6 frames per scene
- Generate detailed image prompt per frame
- Inject character/location details into prompts

REFERENCES:
- Generate on-demand (user clicks per entity)
- Replace AI reference when user uploads
- Archive old references to _archive/
```

---

## DECISION FILTER

When making any decision, ask:
```
1. Does this serve the PRIMARY GOAL?
   - Does it help create visual storyboards?
   - Does it improve entity/world consistency?

2. Does this enable the OPERATIONAL FUNCTIONS?
   - Does it support the ingestion → outline → director flow?
   - Does it give users control at review points?

3. Does this stay within BOUNDARIES?
   - Grok 4.1 Fast for LLM
   - Isaac 0.1 for vision
   - File-based storage
   - Progressive updates

YES to all → Proceed
NO to any  → ⏸ Discuss with user
```

---

DOCUMENT_STATUS: ●_FOUNDATIONAL
TRACE: ●🎯
LAST_VERIFIED: 2026-01-14
