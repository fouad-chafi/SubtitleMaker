# SubtitleMaker

AI-powered subtitle generator optimized for RTX 4070 Super with a modern web interface.

## Features

- High-accuracy transcription using OpenAI Whisper large-v3
- GPU acceleration with CUDA 12.x (optimized for RTX 4070 Super)
- Modern React + TypeScript web interface
- REST API with FastAPI
- Multi-format export (SRT, VTT, ASS, TXT)
- Real-time transcription progress
- Customizable subtitle styles
- 99+ language support

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- CUDA 12.x (for GPU acceleration)
- FFmpeg
- PostgreSQL (optional)
- Redis (optional)

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# Especially change SECRET_KEY

# Run the API server
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The web interface will be available at http://localhost:5173

## Project Structure

```
subtitle-generator/
├── src/                    # Backend source
│   ├── core/               # Core logic (transcriber, formatter)
│   ├── models/             # Data models
│   ├── services/           # Business logic layer
│   ├── utils/              # Utilities
│   └── api/                # FastAPI routes
├── frontend/               # React + TypeScript frontend
├── config/                 # Configuration files
├── tests/                  # Test files
└── docs/                   # Documentation
```

## API Documentation

Once the server is running, visit http://localhost:8000/docs for interactive API documentation.

## Development

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test
```

### Code Quality

```bash
# Format code
black src/
ruff check src/

# Type checking
mypy src/
```

## License

MIT License - see LICENSE file for details
