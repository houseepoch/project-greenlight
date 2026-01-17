# Project Greenlight

AI-powered cinematic storyboard generator that transforms scripts and documents into visual storyboards.

## Features

- **Document Ingestion** - Upload scripts, synopses, PDFs, images
- **Entity Extraction** - Automatic character, location, and prop detection
- **World Bible Builder** - Generate world documentation with descriptions
- **Story Outline** - Multiple narrative approaches
- **Director Pipeline** - Frame-by-frame breakdowns
- **Storyboard Generation** - Cinematic frames with reference images

## Requirements

- **Python 3.10+** - [Download](https://python.org)
- **Node.js 18+** - [Download](https://nodejs.org)
- **API Keys:**
  - xAI API key from [x.ai](https://x.ai)
  - Replicate API token from [replicate.com](https://replicate.com)

## Quick Start

### 1. Install Prerequisites

Download and install Python and Node.js from the links above.

**Important:** When installing Python, check "Add Python to PATH".

### 2. Run Setup

```
Double-click: setup.bat
```

This creates a virtual environment and installs all dependencies.

### 3. Add API Keys

Open `.env` in a text editor and add your keys:

```
XAI_API_KEY=xai-your-key-here
REPLICATE_API_TOKEN=r8_your-token-here
```

### 4. Start the App

```
Double-click: greenlight.bat
```

Opens http://localhost:3000 in your browser.

### 5. Stop the App

```
Double-click: stop.bat
```

## Manual Start

If you prefer command line:

```bash
# Terminal 1 - Backend
venv\Scripts\activate
python -m greenlight server

# Terminal 2 - Frontend
cd web
npm run dev
```

## Project Structure

```
project-greenlight/
├── greenlight/          # Python backend
│   ├── api/             # FastAPI endpoints
│   ├── core/            # Core modules (LLM, image gen)
│   ├── pipelines/       # Pipeline implementations
│   └── utils/           # Utilities
├── web/                 # Next.js frontend
│   └── src/
│       ├── app/         # Pages
│       ├── components/  # React components
│       └── lib/         # Utilities
├── projects/            # Your projects (created on first run)
├── setup.bat            # First-time setup
├── greenlight.bat       # Start app
├── stop.bat             # Stop app
├── requirements.txt     # Python dependencies
└── .env.example         # Environment template
```

## Tech Stack

**Backend:** Python, FastAPI, Grok (xAI), Replicate

**Frontend:** Next.js 14, TypeScript, Tailwind CSS

## License

MIT License
