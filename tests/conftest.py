"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch
import os

# Set test environment
os.environ['TESTING'] = 'true'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
os.environ['GOOGLE_CLOUD_LOCATION'] = 'us-central1'

# Import after setting environment variables
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.api.database import Base, get_db
from src.api.main import app
from src.api.auth import get_current_user
from src.api.models import User


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database for each test function."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture(scope="function")
def override_get_db(test_db):
    """Override the get_db dependency with test database."""
    async def _override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$KIXxPfnK6JpG8KPK8KPK8KPK8KPK8KPK8KPK8KPK8KPK8KPK8KPK8",
        is_active=True,
        is_verified=True,
        role="researcher"
    )


@pytest.fixture
def authenticated_client(test_user, override_get_db):
    """Create a test client with authentication."""
    def override_current_user():
        return test_user
    
    app.dependency_overrides[get_current_user] = override_current_user
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(override_get_db):
    """Create a test client without authentication."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_adk():
    """Mock ADK client."""
    with patch('src.api.adk_integration.ParallaxPalADK') as mock:
        adk_instance = AsyncMock()
        mock.return_value = adk_instance
        
        # Mock stream_research method
        async def mock_stream_research(*args, **kwargs):
            yield {
                'type': 'start',
                'agent': 'orchestrator',
                'content': 'Starting research',
                'progress': 0
            }
            yield {
                'type': 'complete',
                'agent': 'orchestrator',
                'content': {'summary': 'Test complete'},
                'progress': 100
            }
        
        adk_instance.stream_research = mock_stream_research
        
        # Mock health check
        adk_instance.get_agent_health = AsyncMock(return_value={
            'overall_status': 'healthy',
            'agents': {
                'orchestrator': {'status': 'healthy'},
                'retrieval': {'status': 'healthy'},
                'analysis': {'status': 'healthy'},
                'citation': {'status': 'healthy'},
                'knowledge_graph': {'status': 'healthy'}
            }
        })
        
        yield adk_instance


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('src.api.cache.redis_client') as mock:
        redis_instance = AsyncMock()
        mock.return_value = redis_instance
        
        # Mock basic Redis operations
        redis_instance.get = AsyncMock(return_value=None)
        redis_instance.set = AsyncMock(return_value=True)
        redis_instance.delete = AsyncMock(return_value=1)
        redis_instance.exists = AsyncMock(return_value=0)
        redis_instance.expire = AsyncMock(return_value=True)
        
        yield redis_instance


@pytest.fixture
def mock_stripe():
    """Mock Stripe client."""
    with patch('stripe.Customer') as customer_mock, \
         patch('stripe.Subscription') as subscription_mock, \
         patch('stripe.PaymentMethod') as payment_mock:
        
        # Mock customer creation
        customer_mock.create = Mock(return_value=Mock(id='cus_test123'))
        
        # Mock subscription creation
        subscription_mock.create = Mock(return_value=Mock(
            id='sub_test123',
            status='active',
            current_period_end=1234567890
        ))
        
        # Mock payment method
        payment_mock.attach = Mock()
        
        yield {
            'customer': customer_mock,
            'subscription': subscription_mock,
            'payment': payment_mock
        }


@pytest.fixture
def mock_email():
    """Mock email service."""
    with patch('src.api.services.email.send_email') as mock:
        mock.return_value = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def sample_research_query():
    """Sample research query for testing."""
    return {
        "query": "What is quantum computing?",
        "mode": "comprehensive",
        "focus_areas": ["technology", "science"],
        "language": "en"
    }


@pytest.fixture
def sample_websocket_message():
    """Sample WebSocket message for testing."""
    return {
        "type": "research_query",
        "data": {
            "query": "Test research query",
            "mode": "quick"
        },
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }