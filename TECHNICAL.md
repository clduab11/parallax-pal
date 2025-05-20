# Parallax Pal Technical Documentation

Comprehensive technical documentation for setting up, developing, and deploying Parallax Pal.

## Tech Stack Overview

Parallax Pal combines modern technologies to deliver a powerful research assistant platform. Below is a comprehensive breakdown of our technical architecture.

### Frontend Architecture
- **Framework**: React 18+ with TypeScript 5.0+
- **Styling**: Tailwind CSS 3.3+ with custom terminal-inspired theme
- **State Management**: Redux Toolkit for global state, React Query for API data
- **Real-time Updates**: WebSocket integration with reconnection handling
- **UI Components**: Custom terminal-inspired component library
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Accessibility**: WCAG 2.1 AA compliant
- **Testing**: Jest, React Testing Library, and Cypress for E2E tests

### Backend Architecture
- **API Framework**: FastAPI 0.100.0+ (Python 3.11+)
- **Database**: PostgreSQL 15+ with SQLAlchemy ORM
- **Caching**: Redis 7+ with custom cache invalidation strategies
- **Migrations**: Alembic for database schema versioning
- **Authentication**: OAuth2 with JWT tokens and refresh token rotation
- **Payment Processing**: Stripe API integration with webhook handling
- **Email Service**: SMTP integration with templated emails
- **Background Tasks**: Asynchronous task processing with proper error handling
- **Monitoring**: Prometheus metrics, structured logging, and health checks
- **Testing**: pytest for unit and integration tests

## Research System Architecture

### Multi-Model AI Integration
- **Core Engine**: Custom orchestration layer for multiple AI models
- **Supported Models**: OpenAI (GPT-4), Anthropic (Claude), Google (Gemini), Ollama (local models)
- **Model Selection**: Dynamic routing based on query complexity and subscription tier
- **Fallback Mechanism**: Graceful degradation when primary models are unavailable

### Search and Data Processing
- **Web Search**: Integration with multiple search engines for comprehensive results
- **Content Extraction**: HTML parsing and content normalization
- **Data Processing**: NLP pipeline for extracting key information
- **Citation System**: Automatic source tracking and citation generation

### GPU Acceleration
- **Hardware Support**: NVIDIA (CUDA) and Apple (Metal) optimization
- **Resource Management**: Dynamic allocation based on query complexity
- **Batch Processing**: Efficient handling of multiple concurrent requests
- **Monitoring**: Real-time GPU utilization and temperature tracking

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis
- (Optional) NVIDIA GPU for Ollama acceleration

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/clduab11/parallax-pal.git
cd parallax-pal
```

2. Create and activate Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

3. Install Python dependencies:
```bash
cd src/api
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd ../frontend
npm install
```

5. Copy example environment files:
```bash
cp .env.example .env
```

6. Update environment variables in `.env`:
```env
# Application
DEBUG=true
SECRET_KEY=your-secret-key
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/parallaxpal

# Redis
REDIS_URL=redis://localhost:6379/0

# Cache Settings
USE_CACHE=true
CACHE_TTL=86400  # 24 hours in seconds

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
# ... other OAuth provider settings

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

### Database Setup

1. Create PostgreSQL database:
```bash
createdb parallaxpal
```

2. Run database migrations:
```bash
cd src/api
alembic upgrade head
```

### Running the Application

1. Start the backend server:
```bash
cd src/api
uvicorn main:app --reload --port 8000
```

2. Start the frontend development server:
```bash
cd src/frontend
npm start
```

3. Access the application:
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- API Redoc: http://localhost:8000/redoc

## Development Guidelines

### Code Style

- Backend: Black + isort + flake8
- Frontend: ESLint + Prettier

### Testing

Backend tests:
```bash
cd src/api
pytest
```

Frontend tests:
```bash
cd src/frontend
npm test
```

### Database Migrations

```bash
cd src/api
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

## API Documentation

### Authentication

- OAuth2 with multiple providers
- JWT token-based authentication
- Refresh token rotation
- MFA support

### Rate Limiting

- Per-user rate limits
- Burst allowance
- Premium tier limits

### WebSocket Events

- Research updates
- GPU status monitoring
- Real-time analytics

## Deployment

### Production Setup

1. Build frontend:
```bash
cd src/frontend
npm run build
```

2. Configure production environment variables
3. Run database migrations
4. Start application with production server (e.g., Gunicorn)

### Docker Deployment

1. Build images:
```bash
docker-compose build
```

2. Start services:
```bash
docker-compose up -d
```

### Monitoring

- Application metrics: http://localhost:8000/metrics
- Health check: http://localhost:8000/health
- Logs: Check `logs/` directory

## Security Considerations

### Authentication
- OAuth2 implementation
- Token management
- Session security
- MFA implementation

### Data Protection
- Input validation
- SQL injection prevention
- XSS protection
- CSRF protection

### API Security
- Rate limiting
- Request validation
- Error handling
- Audit logging

## Performance Optimization

### Caching Strategy
- Redis caching for API endpoints
- File-based caching for research results
- Intelligent caching of research queries and analyses
- Cache invalidation based on time-to-live (TTL)
- Force refresh capability to bypass cache
- Browser caching for static assets
- Static asset optimization
- Query optimization

### GPU Acceleration
- Model loading
- Batch processing
- Memory management
- Error handling

## Troubleshooting

### Common Issues
- Database connection issues
- OAuth configuration
- GPU detection problems
- WebSocket connectivity

### Debugging Tools
- Application logs
- Database logs
- GPU monitoring
- Network debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Pull Request Guidelines
- Include tests
- Update documentation
- Follow code style
- Add changelog entry

## License

### Proprietary License

This project is licensed under a proprietary license by Parallax Analytics, LLC. All rights reserved.

See the [LICENSE](LICENSE) file for details on the commercial license terms and conditions.

### Third-Party Components

Parallax Pal incorporates several open-source components, each governed by its respective license:

- React: MIT License
- FastAPI: MIT License
- SQLAlchemy: MIT License
- Alembic: MIT License
- Tailwind CSS: MIT License

Full license details for all third-party components are available in the `THIRD_PARTY_LICENSES.md` file.

### Commercial Usage

Commercial usage of Parallax Pal requires a valid license from Parallax Analytics, LLC. For licensing inquiries, please contact licensing@parallaxanalytics.com.