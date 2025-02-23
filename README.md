# Parallax Pal

A powerful research and analytics platform with FastAPI backend and React/TypeScript frontend, featuring advanced GPU acceleration support.

## Key Features

- **Advanced GPU Acceleration**
  - NVIDIA GPU support with dynamic VRAM management
  - Apple Silicon Metal support for optimized performance
  - Automatic model selection based on available hardware
  - Real-time GPU monitoring and status

- **Intelligent Research**
  - Multi-model analysis and synthesis
  - Real-time research task tracking
  - Advanced caching and optimization
  - Customizable research workflows

- **Enterprise Infrastructure**
  - Secure JWT-based authentication with refresh tokens
  - Multi-factor authentication (MFA)
  - Email verification and password reset
  - Role-based access control
  - PostgreSQL database with Redis caching
  - Comprehensive monitoring with Prometheus and Grafana
  - Docker-based deployment

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.10+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)
- Stripe account for payment processing
- NVIDIA GPU or Apple Silicon device (optional, for hardware acceleration)

## Configuration

1. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Configure the following environment variables:
   - Database credentials
   - Redis connection
   - JWT secret key
   - Stripe API keys
   - Email service credentials
   - Frontend URL

## Development Setup

1. Install backend dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

2. Install frontend dependencies:
   ```bash
   cd src/frontend
   npm install
   ```

3. Start the development servers:
   ```bash
   # Terminal 1 - Backend
   uvicorn api.main:app --reload --port 8000

   # Terminal 2 - Frontend
   cd src/frontend
   npm start
   ```

## Docker Deployment

1. Build and start the services:
   ```bash
   docker-compose up -d --build
   ```

2. Initialize the database:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

3. Create an admin user:
   ```bash
   docker-compose exec backend python scripts/create_admin.py
   ```

The application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Subscription Plans

The platform offers four subscription tiers:

1. Free Tier (Ad-Supported)
   - Basic research capabilities
   - Limited API access
   - Community support
   - Ad-supported experience
   - Data collection and analytics
   Price: Free

2. Basic Plan (+23%)
   - All Free Tier features
   - Ad-free experience
   - Basic research capabilities
   - Standard API access
   - Email support
   - Basic analytics
   Price: $49/month

3. Pro Plan (+23%)
   - All Basic Plan features
   - Advanced research features
   - Full API access
   - Priority support
   - Custom analytics
   - GPU acceleration
   - Advanced data exports
   Price: $99/month

4. Enterprise Plan (+23%)
   - All Pro Plan features
   - Unlimited research
   - Custom integrations
   - Dedicated support
   - Advanced analytics
   - Custom features
   - Priority GPU access
   - White-label options
   Price: Starting at $499/month

## Data Collection & Privacy

For users on the Free (Ad-Supported) Tier:
- Usage patterns and behavior analytics
- Search and research topic analysis
- Demographic information
- Device and browser data
- Interaction metrics

This data is used to:
- Improve service quality
- Personalize advertising
- Enhance user experience
- Generate aggregated insights
- Share with advertising partners

Paid tiers have limited data collection focused only on service improvement.

## Payment Processing

Payment processing is handled through Stripe:
1. Users can add and manage payment methods
2. Subscription management with automatic billing
3. Secure payment processing
4. Automatic invoice generation
5. Payment failure handling

## Hardware Acceleration

The platform supports multiple GPU architectures:

1. NVIDIA GPUs
   - Dynamic VRAM management
   - Multi-model support
   - Automatic model selection
   - Real-time performance monitoring

2. Apple Silicon (Metal)
   - Native Metal API support
   - Optimized for M1/M2/M3 chips
   - Shared memory management
   - Power-efficient inference

3. CPU Fallback
   - Automatic fallback for non-GPU systems
   - Optimized CPU inference
   - Resource-aware scheduling

## Monitoring and Metrics

The platform includes comprehensive monitoring:
1. Application metrics via Prometheus
2. Visualization through Grafana
3. Real-time performance monitoring
4. Custom dashboards for:
   - User activity
   - Research tasks
   - System performance
   - API usage
   - GPU utilization
   - Subscription status

## Security Features

1. Authentication:
   - JWT with refresh tokens
   - Multi-factor authentication
   - Email verification
   - Password reset functionality

2. Authorization:
   - Role-based access control
   - Fine-grained permissions
   - API key management

3. Data Protection:
   - Data encryption at rest
   - Secure communication (HTTPS)
   - Rate limiting
   - Input validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
