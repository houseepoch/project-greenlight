# Project Constants (Immutable)

> **These facts do not change during development.**
> **Only modify via `/set-project-context` command.**

---

## LOCKED DECISIONS ⚓

| ID | Constant | Value | Locked Date |
|----|----------|-------|-------------|
| ⚓001 | Project Name | Project Greenlight | 2026-01-14 |
| ⚓002 | Primary Language (Backend) | Python 3.11+ | 2026-01-14 |
| ⚓003 | Primary Language (Frontend) | TypeScript | 2026-01-14 |
| ⚓004 | Backend Framework | FastAPI | 2026-01-14 |
| ⚓005 | Frontend Framework | Next.js 14 | 2026-01-14 |
| ⚓006 | Database | File System (No DB) | 2026-01-14 |
| ⚓007 | Primary LLM | Grok 4.1 Fast (xAI) | 2026-01-14 |
| ⚓008 | Vision Model | Isaac 0.1 (Replicate) | 2026-01-14 |
| ⚓009 | Image Generation | Seedream 4.5 / Flux 2 Pro | 2026-01-14 |

---

## API PROVIDERS ⚓

### LLM Providers

| Provider | Model | Identifier | Purpose |
|----------|-------|------------|---------|
| **xAI** | Grok 4.1 Fast | `grok-4-1-fast` | Primary LLM (entity extraction, world building, writing) |
| Google | Gemini 3 Pro | `gemini-3-pro` | Alternative LLM |
| Anthropic | Claude Sonnet 4 | `claude-sonnet-4` | Optional fallback |

**Primary LLM API:**
```
Provider: xAI
Endpoint: https://api.x.ai/v1/
Model: grok-4-1-fast
Context: 2M tokens
Features: Agentic tool calling, reasoning
Env Var: XAI_API_KEY
```

### Vision Provider

| Provider | Model | Identifier | Purpose |
|----------|-------|------------|---------|
| **Replicate** | Isaac 0.1 | `perceptron-ai-inc/isaac-0.1` | Image analysis, entity extraction |

**Vision API:**
```
Provider: Replicate
Model: perceptron-ai-inc/isaac-0.1
Parameters: 2B
Features: Grounded perception, OCR, spatial reasoning
Env Var: REPLICATE_API_TOKEN
```

### Image Generation

| Provider | Model | Identifier | Purpose |
|----------|-------|------------|---------|
| **Replicate** | Seedream 4.5 | `bytedance/seedream-4.5` | Primary image gen (fast, cinematic) |
| **Replicate** | Flux 2 Pro | `black-forest-labs/flux-2-pro` | Premium image gen (4MP, high-fidelity) |
| Google | Gemini Image | `gemini-3-pro-image-preview` | Alternative (Nano Banana Pro) |

**Image API:**
```
Provider: Replicate
Primary Model: bytedance/seedream-4.5
Premium Model: black-forest-labs/flux-2-pro
Env Var: REPLICATE_API_TOKEN
```

---

## IMMUTABLE CONSTRAINTS

### Technical Constraints
```
- No database (file-based only via JSON)
- Async-first Python backend (asyncio)
- Single LLM provider per pipeline run
- Progressive updates via polling (no WebSockets)
- Fixed token chunking (500-1000 tokens, 10% overlap)
```

### API Rate Limits
```
- Respect per-provider rate limits
- Implement retry with exponential backoff
- Max 3 retries per request
- Default timeout: 120 seconds
```

### File Formats Supported
```
Documents: .txt, .md, .pdf, .docx
Images: .png, .jpg, .jpeg, .gif, .webp
Archives: .zip (auto-extracted)
```

---

## MODEL ALIASES

```python
# Quick reference for code usage
from greenlight.core.config import LLMModels, ImageModels, resolve_model

# LLM
LLMModels.GROK_4_1_FAST      # "grok-4-1-fast"
LLMModels.GEMINI_3_PRO       # "gemini-3-pro"
LLMModels.CLAUDE_SONNET      # "claude-sonnet-4"

# Image
ImageModels.ISAAC_01         # "perceptron-ai-inc/isaac-0.1"
ImageModels.SEEDREAM_45      # "bytedance/seedream-4.5"
ImageModels.FLUX_2_PRO       # "black-forest-labs/flux-2-pro"
ImageModels.GEMINI_IMAGE     # "gemini-3-pro-image-preview"

# Resolve alias to full identifier
resolve_model("grok")        # -> "grok-4-1-fast"
resolve_model("seedream")    # -> "bytedance/seedream-4.5"
```

---

## ENV CONFIGURATION

Required environment variables in `.env`:
```bash
# LLM (Required - at least one)
XAI_API_KEY=xai-...          # Grok 4.1 Fast
GEMINI_API_KEY=...           # Gemini 3 Pro (optional)
ANTHROPIC_API_KEY=sk-ant-... # Claude (optional)

# Image/Vision (Required)
REPLICATE_API_TOKEN=r8_...   # Isaac 0.1 + Seedream/Flux
```

---

## MODIFICATION LOG

| Date | Change | Changed By | Reason |
|------|--------|------------|--------|
| 2026-01-14 | Initial constants locked | Claude | Project setup |
| 2026-01-14 | Model identifiers verified | Claude | API research |

**Note:** Changes require `/set-project-context` command with explicit user approval ⏸⏸

---

DOCUMENT_STATUS: ⚓_IMMUTABLE
TRACE: ●⚓
LAST_MODIFIED: 2026-01-14
MODIFIED_VIA: /sync-context
