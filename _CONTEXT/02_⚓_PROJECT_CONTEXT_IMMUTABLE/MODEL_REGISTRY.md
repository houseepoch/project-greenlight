# Model Registry (Updated 2026-01-14)

> **Canonical model identifiers for all AI services.**
> **Research verified from official sources.**

---

## LLM MODELS

### xAI Grok (Primary)

| Model | Identifier | Context | Features |
|-------|------------|---------|----------|
| **Grok 4.1 Fast** | `grok-4-1-fast` | 2M tokens | Agentic tool calling, reasoning |
| Grok 4.1 Fast (Reasoning) | `grok-4-1-fast-reasoning` | 2M tokens | Full reasoning chain |
| Grok 4.1 Fast (Non-Reasoning) | `grok-4-1-fast-non-reasoning` | 2M tokens | Fast, no CoT |
| Grok 4 | `grok-4` | - | Base model |

**API Endpoint:** `https://api.x.ai/v1/`
**Key Variable:** `XAI_API_KEY`
**Docs:** https://docs.x.ai/docs/models

### Google Gemini (Alternative)

| Model | Identifier | Features |
|-------|------------|----------|
| Gemini 3 Pro | `gemini-3-pro` | General LLM |

**API Endpoint:** Google AI API
**Key Variable:** `GEMINI_API_KEY`
**Docs:** https://ai.google.dev/gemini-api/docs/models

### Anthropic Claude (Optional)

| Model | Identifier | Features |
|-------|------------|----------|
| Claude Haiku 4.5 | `claude-haiku-4.5` | Fast, efficient |
| Claude Sonnet 4 | `claude-sonnet-4` | Balanced |
| Claude Opus 4.5 | `claude-opus-4.5` | Most capable |

**API Endpoint:** `https://api.anthropic.com/`
**Key Variable:** `ANTHROPIC_API_KEY`

---

## IMAGE MODELS (Replicate)

### Vision/Analysis

| Model | Identifier | Params | Use Case |
|-------|------------|--------|----------|
| **Isaac 0.1** | `perceptron-ai-inc/isaac-0.1` | 2B | Grounded perception, OCR, entity extraction |

**Features:**
- Spatial reasoning with bounding boxes
- OCR for text in images
- Entity extraction with evidence
- Open-weight VLM

### Text-to-Image Generation

| Model | Identifier | Resolution | Use Case |
|-------|------------|------------|----------|
| **Seedream 4.5** | `bytedance/seedream-4.5` | High | Portraits, cinematic, fast |
| **Flux 2 Pro** | `black-forest-labs/flux-2-pro` | 4MP | High-fidelity, accurate details |
| Flux 2 Dev | `black-forest-labs/flux-2-dev` | 4MP | Development/testing |

**Seedream 4.5 Features:**
- Cinematic aesthetics
- Strong spatial reasoning
- Precise instruction following
- Text rendering capability

**Flux 2 Pro Features:**
- Mistral-3 24B VLM backbone
- 4MP resolution output
- Accurate hands, faces, fabrics
- ~6 second generation
- Cost: $0.015 + $0.015/megapixel

### Google Image Generation

| Model | Identifier | Resolution | Use Case |
|-------|------------|------------|----------|
| Gemini 3 Pro Image | `gemini-3-pro-image-preview` | 4K | Professional assets, text rendering |

**Features (Nano Banana Pro):**
- 1K/2K/4K output
- Advanced text rendering
- Multi-image reference mixing (up to 14)
- Google Search grounding

**Key Variable:** `GEMINI_API_KEY`

---

## REPLICATE API

**Base URL:** `https://api.replicate.com/v1/`
**Key Variable:** `REPLICATE_API_TOKEN`

### Prediction Flow
```
POST /models/{owner}/{model}/predictions
  -> Poll GET /predictions/{id}
  -> Status: starting -> processing -> succeeded/failed
```

### Model URL Format
```
https://replicate.com/{owner}/{model}
API: https://api.replicate.com/v1/models/{owner}/{model}/predictions
```

---

## MODEL ALIASES (config.py)

```python
# LLM aliases
"grok"         -> "grok-4-1-fast"
"grok-fast"    -> "grok-4-1-fast"
"gemini"       -> "gemini-3-pro"
"claude"       -> "claude-sonnet-4"
"claude-haiku" -> "claude-haiku-4.5"
"claude-opus"  -> "claude-opus-4.5"

# Image aliases
"isaac"        -> "perceptron-ai-inc/isaac-0.1"
"seedream"     -> "bytedance/seedream-4.5"
"flux"         -> "black-forest-labs/flux-2-pro"
"flux-pro"     -> "black-forest-labs/flux-2-pro"
"flux-dev"     -> "black-forest-labs/flux-2-dev"
"gemini-image" -> "gemini-3-pro-image-preview"
"nano-banana"  -> "gemini-3-pro-image-preview"
```

---

## DEFAULT CONFIGURATION

```python
default_llm = "grok-4-1-fast"       # xAI Grok 4.1 Fast
default_image_model = "seedream"    # Seedream 4.5
```

---

## SOURCES

- xAI Docs: https://docs.x.ai/docs/models
- xAI Grok 4.1 Fast: https://x.ai/news/grok-4-1-fast
- Google Gemini 3: https://ai.google.dev/gemini-api/docs/gemini-3
- Replicate Isaac 0.1: https://replicate.com/blog/isaac-01
- Replicate Seedream 4.5: https://replicate.com/bytedance/seedream-4.5
- Replicate Flux 2 Pro: https://replicate.com/black-forest-labs/flux-2-pro
- Black Forest Labs FLUX.2: https://bfl.ai/blog/flux-2

---

DOCUMENT_STATUS: ⚓_REFERENCE
TRACE: ●⚓📍
LAST_VERIFIED: 2026-01-14
