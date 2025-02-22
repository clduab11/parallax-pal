# Parallax Pal

A production-ready research and analytics platform that transforms raw data into actionable insights. Originally a CLI tool, now evolved into a scalable web application with real-time research capabilities and analytics integration.

## Features

### Core Platform
- FastAPI-based REST API with async processing
- React/TypeScript frontend with real-time updates
- PostgreSQL database with connection pooling
- Redis caching for enhanced performance
- Asynchronous research task processing
- Real-time research progress updates
- Integration with Parallax Analytics platform

### Security & Authentication
- JWT-based authentication
- Role-based access control (RBAC)
- Rate limiting and DoS protection
- CORS protection
- SQL injection prevention
- XSS protection
- CSRF protection
- Secure password hashing

### Monitoring & Performance
- Prometheus metrics integration
- Structured JSON logging
- Health check endpoints
- Connection pool management
- Query performance monitoring
- Real-time system metrics
- Error tracking and reporting

### Quality & Testing
- Comprehensive test coverage
- End-to-end testing suite
- Integration tests
- Unit testing for all components
- Performance benchmarking
- Security vulnerability scanning
- Load testing capabilities

## Architecture

```
parallax-pal/
├── src/
│   ├── api/                # Backend FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py        # API entry point
│   │   ├── auth.py        # Authentication
│   │   ├── models.py      # Database models
│   │   ├── database.py    # Database configuration
│   │   ├── config.py      # Application configuration
│   │   ├── cache.py       # Redis caching
│   │   ├── monitoring.py  # Metrics and logging
│   │   └── research.py    # Research task handling
│   │
│   └── frontend/          # React/TypeScript frontend
│       ├── src/
│       │   ├── components/ # Reusable UI components
│       │   ├── contexts/   # React contexts (auth, etc.)
│       │   ├── pages/     # Page components
│       │   ├── services/  # API integration
│       │   └── types/     # TypeScript definitions
│       ├── package.json
│       └── tsconfig.json
```

## Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL 13+
- Redis 6+

## Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
python -m alembic upgrade head
```

5. Start the API server:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at http://localhost:8000  
Swagger documentation at http://localhost:8000/api/docs  
ReDoc documentation at http://localhost:8000/api/redoc

## Frontend Setup

1. Navigate to the frontend directory:
```bash
cd src/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at http://localhost:3000

## Production Deployment

### Backend

1. Set environment variables:
- `ENV=production`
- `DEBUG=False`
- Configure secure `SECRET_KEY`
- Set production `DATABASE_URL`
- Configure `REDIS_URL`
- Set valid `FRONTEND_URL` for CORS
- Configure `METRICS_PREFIX`
- Set up `ERROR_REPORTING_EMAIL`

2. Run database migrations:
```bash
alembic upgrade head
```

3. Start using gunicorn with multiple workers:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --log-level info --access-logfile - src.api.main:app
```

### Frontend

1. Build the production bundle:
```bash
cd src/frontend
npm run build
```

2. Serve using nginx or similar web server, with configuration for:
- Caching static assets
- Gzip compression
- SSL/TLS
- HTTP/2
- Security headers

## Monitoring

### Metrics
- Prometheus metrics available at `/metrics`
- Connection pool statistics
- Request latency tracking
- Error rate monitoring
- Task queue metrics

### Logging
- Structured JSON logs
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging
- Error tracking
- Performance metrics

### Health Checks
- Basic health: `/`
- Detailed health: `/api/health`
- Database connectivity
- Redis connection status
- System resources

## Testing

### Backend
```bash
# Run all tests with coverage
pytest --cov=src/api

# Run specific test categories
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

### Frontend
```bash
cd src/frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific tests
npm test -- --watch
```

## API Documentation

- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/api/openapi.json`

Includes detailed descriptions of:
- Authentication flows
- Research endpoints
- Analytics integration
- Error responses
- Rate limits
- Request/response schemas

## Environment Variables

See `.env.example` for all available configuration options, including:
- Application settings
- Security configurations
- Database settings
- Redis configuration
- Monitoring options
- Feature flags
- Integration settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

Please ensure:
- All tests pass
- Code follows style guidelines
- Documentation is updated
- Changes are backwards compatible

## License

This project is licensed under the MIT License - see the LICENSE file for details.
