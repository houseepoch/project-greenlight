# Project Greenlight

AI-powered cinematic storyboard generator that transforms scripts and documents into visual storyboards.

## Features

- **Document Ingestion** - Upload scripts, synopses, PDFs, images, and more
- **Entity Extraction** - Automatic character, location, and prop detection with 3-way consensus
- **World Bible Builder** - Generate comprehensive world documentation with character descriptions, locations, and props
- **Story Outline** - Multiple narrative approaches (dramatic arc, mystery, character journey)
- **Director Pipeline** - Full prose scenes with frame-by-frame breakdowns
- **Reference Images** - On-demand AI generation for visual consistency
- **Storyboard Generation** - Cinematic frame generation with reference image integration

## Tech Stack

**Backend:**
- Python 3.10+ with FastAPI
- Grok 4.1 Fast (xAI) - Primary LLM
- Isaac 0.1 (Replicate) - Vision model
- Seedream 4.5 / Flux 2 Pro (Replicate) - Image generation

**Frontend:**
- Next.js 14 with TypeScript
- Tailwind CSS

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys for xAI and Replicate

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/houseepoch/project-greenlight.git
   cd project-greenlight
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Install frontend dependencies:**
   ```bash
   cd web
   npm install
   cd ..
   ```

### Running the Application

**Option 1: Use the launcher script (Windows)**
```bash
launch.bat
```

**Option 2: Run manually**

Terminal 1 - Backend:
```bash
python -m greenlight
# or: uvicorn greenlight.api.main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd web
npm run dev
```

Access the application at http://localhost:3000

## Project Structure

```
project-greenlight/
├── greenlight/              # Python backend package
│   ├── api/                 # FastAPI endpoints
│   │   ├── main.py          # App entry point
│   │   ├── ingestion.py     # Document upload/processing
│   │   ├── pipelines.py     # Pipeline orchestration
│   │   ├── projects.py      # Project management
│   │   └── images.py        # Image serving
│   ├── core/                # Core modules
│   │   ├── config.py        # Settings and model registry
│   │   ├── llm.py           # LLM client (Grok)
│   │   ├── models.py        # Data models
│   │   ├── ingestion.py     # Document processing
│   │   ├── isaac.py         # Vision model client
│   │   └── image_gen.py     # Image generation
│   ├── pipelines/           # Pipeline implementations
│   │   ├── world_builder.py # World bible generation
│   │   ├── writer.py        # Story writing
│   │   ├── director.py      # Frame breakdown
│   │   ├── outline_generator.py
│   │   ├── references.py    # Reference image gen
│   │   └── storyboard.py    # Storyboard generation
│   └── utils/               # Utility functions
├── web/                     # Next.js frontend
│   └── src/
│       ├── app/             # App router pages
│       ├── components/      # React components
│       └── lib/             # Utilities
├── tests/                   # Test suite
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── pyproject.toml           # Python project config
```

## API Endpoints

### Ingestion
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ingestion/upload` | POST | Upload files |
| `/api/ingestion/start` | POST | Start ingestion pipeline |
| `/api/ingestion/entities/{path}` | GET | Get extracted entities |
| `/api/ingestion/confirm-entities` | POST | Confirm entity selections |

### Pipelines
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pipelines/world-builder` | POST | Start world builder |
| `/api/pipelines/writer` | POST | Generate story outline |
| `/api/pipelines/director` | POST | Generate visual script |
| `/api/pipelines/storyboard` | POST | Generate storyboard frames |
| `/api/pipelines/storyboard/scene/{n}` | POST | Generate single scene |
| `/api/pipelines/storyboard/frame/{id}` | POST | Regenerate frame |

## Pipeline Flow

```
Documents/Images Upload
        │
        ▼
┌─────────────────────┐
│  INGESTION          │  Extract text, analyze images,
│  Pipeline           │  3-way consensus entity extraction
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  ENTITY             │  User reviews and confirms
│  Confirmation       │  characters, locations, props
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  WORLD BIBLE        │  Generate descriptions
│  Builder            │  (10-24 words per field)
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  WRITER             │  Generate story outline
│  Pipeline           │  with scene breakdowns
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  DIRECTOR           │  Full prose + frame-by-frame
│  Pipeline           │  breakdown with 250-350 word prompts
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  STORYBOARD         │  Generate cinematic frames
│  Pipeline           │  with reference image integration
└─────────────────────┘
```

## Supported File Formats

- **Documents:** `.txt`, `.md`, `.pdf`, `.docx`
- **Images:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`
- **Archives:** `.zip` (auto-extracted)

## Image Generation Models

| Model | Provider | Best For |
|-------|----------|----------|
| Flux 2 Pro | Replicate | High quality, character consistency |
| Seedream 4.5 | Replicate | Fast, excellent likeness |
| Nano Banana Pro | Gemini | Fast, good quality |

## License

MIT License - See [LICENSE](LICENSE) for details.
