# Parallax Pal Technical Documentation

Comprehensive technical documentation for setting up, developing, and deploying Parallax Pal.

## Tech Stack

### Frontend
- React with TypeScript
- Tailwind CSS for styling
- Terminal-inspired components
- Real-time WebSocket updates
- Responsive design

### Backend
- FastAPI (Python)
- PostgreSQL database
- Redis caching
- Alembic migrations
- OAuth2 authentication
- Stripe integration
- Email notifications
- Background tasks

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
- Redis caching
- Browser caching
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.