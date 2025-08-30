# NVIDIA Documentation MCP Server

A FastAPI-based Multi-Process Communication Server with NVIDIA Documentation Proxy functionality.

## Features

- **Documentation Ingestion**: Automated scraping of NVIDIA product documentation (GPUs, transceivers, cabling, network cards, software)
- **RESTful API**: Search and retrieve documentation with full-text search capabilities
- **Caching**: Redis-based caching for improved performance
- **Scheduled Updates**: Daily automatic documentation updates using APScheduler
- **MongoDB Storage**: Scalable document storage with text search indexes

## Tech Stack

- **Backend**: Python 3.9+ with FastAPI
- **Database**: MongoDB with text search indexes
- **Cache**: Redis with 10-minute TTL
- **Scheduler**: APScheduler for daily ingestion
- **Web Scraping**: BeautifulSoup4 for content extraction
- **Testing**: pytest with async support

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB (local or cloud)
- Redis (local or cloud)
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nvidia-docs-mcp-server
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB and Redis URLs
   ```

4. **Run the application**
   ```bash
   uvicorn src.main:app --reload
   ```

### Docker Setup

1. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## API Endpoints

### Documentation Search

```http
GET /api/docs?product_type=GPU&search=performance&page=1&limit=10
```

**Parameters:**
- `product_type`: Filter by product type (GPU, TRANSCEIVER, CABLING, NETWORK_CARD, SOFTWARE)
- `search`: Full-text search query
- `page`: Pagination page number
- `limit`: Items per page (max 100)

### Get Document by ID

```http
GET /api/docs/{document_id}
```

### Get Statistics

```http
GET /api/docs/stats
```

### Trigger Ingestion

```http
POST /api/docs/ingest
```

## Configuration

### Environment Variables

- `MONGODB_URL`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379`)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)

### Scheduler Configuration

The scheduler runs daily at 2:00 AM UTC by default. To modify the schedule, edit `src/cron/schedule.py`:

```python
trigger = CronTrigger(hour=2, minute=0)  # Change to desired schedule
```

## Testing

Run the test suite:

```bash
pytest -v
```

Test coverage includes:
- Document ingestion and scraping
- API endpoints and controllers
- Redis caching functionality
- MongoDB operations
- Scheduler functionality

## Development

### Project Structure

```
src/
├── main.py              # FastAPI application
├── database.py          # MongoDB and Redis connections
├── models/
│   └── document.py      # Pydantic models
├── ingestion/
│   └── docs_ingest.py   # Documentation scraping
├── cron/
│   └── schedule.py      # Scheduled tasks
├── controllers/
│   └── docs_controller.py # API controllers
└── routes/
    └── docs.py          # API routes

__tests__/               # Test files
```

### Adding New Product Types

1. Add the product type to `NVIDIAProduct` enum in `src/ingestion/docs_ingest.py`
2. Add the base URL to `NVIDIAUrls.BASE_URLS`
3. Update the API validation in `src/routes/docs.py`

## Deployment

### Docker Production

```bash
docker build -t nvidia-docs-mcp-server .
docker run -p 8000:8000 \
  -e MONGODB_URL="mongodb://mongodb:27017" \
  -e REDIS_URL="redis://redis:6379" \
  nvidia-docs-mcp-server
```

### Kubernetes

See the `docker-compose.yml` for reference deployment configuration.

## Monitoring

- Health check: `GET /health`
- Metrics: Integrated with Prometheus-style metrics
- Logging: Structured JSON logging

## License

This project is licensed under the MIT License.