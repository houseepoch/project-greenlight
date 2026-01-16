# Tech Stack (Immutable)

> **Locked technology choices for this project.**
> **Only modify via `/set-project-context` command.**

---

## CORE TECHNOLOGIES

### Frontend
| Component | Technology | Version | Locked |
|-----------|------------|---------|--------|
| Framework | Next.js | 14.x | ⚓ |
| Language | TypeScript | 5.x | ⚓ |
| UI Library | Radix UI | latest | ⚓ |
| State Management | Zustand | 4.x | ⚓ |
| Styling | Tailwind CSS | 3.x | ⚓ |
| Icons | Lucide React | latest | ⚓ |

### Backend
| Component | Technology | Version | Locked |
|-----------|------------|---------|--------|
| Runtime | Python | 3.11+ | ⚓ |
| Framework | FastAPI | 0.100+ | ⚓ |
| API Style | REST | - | ⚓ |
| Async | asyncio | stdlib | ⚓ |
| Validation | Pydantic | 2.x | ⚓ |

### AI/ML Services
| Component | Model | Identifier | Provider | Locked |
|-----------|-------|------------|----------|--------|
| LLM (Primary) | Grok 4.1 Fast | `grok-4-1-fast` | xAI API | ⚓ |
| LLM (Alt) | Gemini 3 Pro | `gemini-3-pro` | Google AI | ⚓ |
| Vision | Isaac 0.1 | `perceptron-ai-inc/isaac-0.1` | Replicate | ⚓ |
| Image Gen (Primary) | Seedream 4.5 | `bytedance/seedream-4.5` | Replicate | ⚓ |
| Image Gen (Premium) | Flux 2 Pro | `black-forest-labs/flux-2-pro` | Replicate | ⚓ |
| Image Gen (Alt) | Gemini Image | `gemini-3-pro-image-preview` | Google AI | ⚓ |

### Document Processing
| Component | Technology | Version | Locked |
|-----------|------------|---------|--------|
| PDF | pypdf2 | 3.x | ⚓ |
| DOCX | python-docx | 1.1+ | ⚓ |
| Tokenization | tiktoken | 0.5+ | ⚓ |

### Infrastructure
| Component | Technology | Version | Locked |
|-----------|------------|---------|--------|
| Storage | File System | - | ⚓ |
| API Client | httpx | latest | ⚓ |
| Replicate SDK | replicate | 0.25+ | ⚓ |

---

## DEPENDENCIES

### Backend (Python)
```toml
[project.dependencies]
fastapi = ">=0.100.0"
uvicorn = ">=0.23.0"
pydantic = ">=2.0.0"
httpx = ">=0.24.0"
python-multipart = ">=0.0.6"
pypdf2 = ">=3.0.0"
python-docx = ">=1.1.0"
tiktoken = ">=0.5.0"
replicate = ">=0.25.0"
```

### Frontend (Node.js)
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "zustand": "^4.4.0",
    "@radix-ui/react-dialog": "^1.0.0",
    "@radix-ui/react-tabs": "^1.0.0",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.300.0"
  }
}
```

---

## API KEYS REQUIRED

| Service | Environment Variable | Purpose | Status |
|---------|---------------------|---------|--------|
| xAI (Grok) | `XAI_API_KEY` | Primary LLM (Grok 4.1 Fast) | ✅ Configured |
| Google AI | `GEMINI_API_KEY` | Alt LLM + Image Gen | ✅ Configured |
| Replicate | `REPLICATE_API_TOKEN` | Isaac vision + Seedream/Flux | ✅ Configured |
| Anthropic | `ANTHROPIC_API_KEY` | Optional fallback LLM | ◇ Optional |

---

## RATIONALE

### Why These Choices?

**Grok 4.1 Fast (xAI):**
- 2M token context window
- Optimized for agentic tool calling
- Fast inference for iterative generation
- Cost-effective for multiple parallel calls

**Isaac 0.1 (Replicate):**
- 2B parameter open-weight VLM
- Grounded perception with bounding boxes
- OCR for text in images
- Entity extraction with evidence

**Seedream 4.5 (Replicate):**
- Cinematic aesthetics, strong spatial reasoning
- Fast generation, good for portraits
- Precise instruction following

**Flux 2 Pro (Replicate):**
- 4MP high-fidelity output
- Mistral-3 24B VLM backbone
- Accurate hands, faces, fabrics
- ~6 second generation

**Gemini 3 Pro Image (Google):**
- 4K output with text rendering
- Multi-image reference mixing
- Google Search grounding

**FastAPI:**
- Native async support for parallel LLM calls
- Automatic OpenAPI documentation
- Pydantic integration for validation

**Next.js + Zustand:**
- React ecosystem familiarity
- Server-side rendering capability
- Simple state management pattern

**File-based Storage:**
- No database setup required
- Portable project folders
- Easy debugging and inspection

**Fixed Token Chunking:**
- Predictable chunk sizes
- Consistent LLM context usage
- Simple overlap implementation

---

## CONSTRAINTS

```
- No database (file-based only)
- Single LLM provider (Grok 4.1 Fast)
- Single vision provider (Isaac 0.1 via Replicate)
- Async-first Python backend
- Progressive updates via polling (no WebSockets)
```

---

DOCUMENT_STATUS: ⚓_IMMUTABLE
TRACE: ●⚓📍
