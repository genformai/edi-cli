# EDI CLI API - REST Service

REST API service for EDI parsing, validation, and analysis.

## Features

- RESTful API for EDI operations
- Asynchronous processing for large files
- WebSocket support for real-time updates
- Docker containerization
- OpenAPI/Swagger documentation

## Installation

```bash
# Install dependencies
cd apps/api
pip install -r requirements.txt

# Or use Docker
docker build -t edi-cli-api .
```

## Usage

```bash
# Development server
python main.py

# Production with gunicorn
gunicorn main:app --workers 4

# Docker
docker run -p 8000:8000 edi-cli-api
```

## API Endpoints

- `POST /parse` - Parse EDI files
- `POST /validate` - Validate EDI files
- `GET /schemas` - List available schemas
- `GET /health` - Health check

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
python -m pytest

# Start dev server with auto-reload
uvicorn main:app --reload
```

## Integration

The API uses the shared core library located in `../../core/` for:
- Transaction parsers
- Validation engines  
- Schema definitions
- Plugin system

See the [core library documentation](../../core/README.md) for implementation details.