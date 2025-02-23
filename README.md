# Parallax Pal

A full-stack research and analytics platform with a terminal-inspired interface, powered by multiple AI models and GPU acceleration.

## Features

- 🖥️ Terminal-inspired UI with modern UX
- 🤖 Multi-model AI analysis (GPT-4, Claude, Gemini, Ollama)
- ⚡ GPU acceleration for local models
- 🔒 Secure OAuth2 authentication
- 💳 Stripe subscription management
- 📊 Real-time analytics and monitoring
- 🔄 Background task processing
- 📱 Responsive design for all devices

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

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis
- (Optional) NVIDIA GPU for Ollama acceleration

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/parallax-pal.git
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

6. Update environment variables in `.env` with your settings:
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

## Development

### Code Style

- Backend: Black + isort + flake8
- Frontend: ESLint + Prettier

### Running Tests

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

### Creating Database Migrations

```bash
cd src/api
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

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

## Monitoring

- Application metrics: http://localhost:8000/metrics
- Health check: http://localhost:8000/health
- Logs: Check `logs/` directory

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
