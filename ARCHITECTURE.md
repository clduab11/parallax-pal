# 🏗️ Parallax Pal Architecture

## System Overview

Parallax Pal is a multi-agent research platform built on Google Cloud's Agent Development Kit (ADK). The system uses a hierarchical agent architecture where a master orchestrator coordinates specialized agents for comprehensive research tasks.

## Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        UI[React UI<br/>TypeScript]
        WS[WebSocket Client]
        Voice[Voice Interface]
    end
    
    subgraph "API Gateway"
        FastAPI[FastAPI Server<br/>Python 3.10+]
        Auth[Auth Middleware<br/>JWT + OAuth2]
        RateLimit[Rate Limiter<br/>Redis-based]
        CORS[CORS Middleware]
    end
    
    subgraph "ADK Agent Layer"
        Orchestrator[Orchestrator Agent<br/>Gemini 2.0 Flash]
        Retrieval[Retrieval Agent<br/>Google Search Tool]
        Analysis[Analysis Agent<br/>Code Execution Tool]
        Citation[Citation Agent<br/>Bibliography Generator]
        KG[Knowledge Graph Agent<br/>Entity Extraction]
    end
    
    subgraph "State Management"
        Redis[(Redis Cache<br/>Session State)]
        Firestore[(Cloud Firestore<br/>Persistent Storage)]
        PubSub[Pub/Sub<br/>Event Streaming]
    end
    
    subgraph "Google Cloud Services"
        VertexAI[Vertex AI<br/>Gemini Models]
        CloudRun[Cloud Run<br/>Container Hosting]
        SecretMgr[Secret Manager<br/>Credentials]
        CloudSQL[(Cloud SQL<br/>PostgreSQL)]
        Speech[Cloud Speech API]
        TTS[Text-to-Speech API]
    end
    
    subgraph "Monitoring"
        CloudMon[Cloud Monitoring]
        CloudTrace[Cloud Trace]
        CloudLog[Cloud Logging]
    end
    
    UI --> WS
    WS --> FastAPI
    Voice --> FastAPI
    FastAPI --> Auth
    Auth --> RateLimit
    RateLimit --> Orchestrator
    
    Orchestrator --> Retrieval
    Orchestrator --> Analysis
    Orchestrator --> Citation
    Orchestrator --> KG
    
    Orchestrator --> Redis
    Orchestrator --> Firestore
    Orchestrator --> PubSub
    
    Retrieval --> VertexAI
    Analysis --> VertexAI
    Citation --> VertexAI
    KG --> VertexAI
    
    FastAPI --> CloudSQL
    FastAPI --> SecretMgr
    Voice --> Speech
    Voice --> TTS
    
    FastAPI --> CloudMon
    FastAPI --> CloudTrace
    FastAPI --> CloudLog
```

## Component Architecture

### Frontend Architecture

```mermaid
graph LR
    subgraph "React Application"
        App[App Component]
        Auth[Auth Context]
        Research[Research Interface]
        Voice[Voice Handler]
        KGraph[Knowledge Graph]
        Metrics[Performance Metrics]
    end
    
    subgraph "Services"
        ADK[ADK Service]
        API[API Service]
        Demo[Demo Service]
        Export[Export Service]
    end
    
    subgraph "State Management"
        Context[React Context]
        LocalState[Component State]
        Cache[Local Storage]
    end
    
    App --> Auth
    App --> Research
    Research --> Voice
    Research --> KGraph
    Research --> Metrics
    
    Research --> ADK
    Auth --> API
    Research --> Demo
    KGraph --> Export
    
    ADK --> Context
    API --> LocalState
    Demo --> Cache
```

### Backend Architecture

```mermaid
graph TB
    subgraph "API Layer"
        Main[main_enhanced.py]
        Routes[Route Handlers]
        WS[WebSocket Handler]
        Mid[Middleware Stack]
    end
    
    subgraph "Business Logic"
        ADKInt[ADK Integration]
        AuthSvc[Auth Service]
        StateMgr[State Manager]
        Features[Feature Modules]
    end
    
    subgraph "Data Layer"
        Models[SQLAlchemy Models]
        Redis[Redis Client]
        Firestore[Firestore Client]
    end
    
    Main --> Routes
    Main --> WS
    Main --> Mid
    
    Routes --> ADKInt
    Routes --> AuthSvc
    WS --> StateMgr
    Routes --> Features
    
    ADKInt --> VertexAI
    StateMgr --> Redis
    StateMgr --> Firestore
    AuthSvc --> Models
```

## Agent Hierarchy

### Master Orchestrator
- **Model**: Gemini 2.0 Flash
- **Temperature**: 0.7
- **Role**: Coordinates all research activities
- **Responsibilities**:
  - Query decomposition
  - Task delegation
  - Progress monitoring
  - Result synthesis
  - Error handling

### Specialized Agents

#### 1. Retrieval Agent
- **Model**: Gemini 2.0 Flash
- **Temperature**: 0.3 (factual accuracy)
- **Tools**: Google Search API
- **Responsibilities**:
  - Web search with domain filtering
  - Source credibility assessment
  - Content extraction
  - Metadata collection

#### 2. Analysis Agent
- **Model**: Gemini 2.0 Flash
- **Temperature**: 0.5 (balanced)
- **Tools**: Code Execution
- **Responsibilities**:
  - Content synthesis
  - Pattern identification
  - Statistical analysis
  - Insight generation

#### 3. Citation Agent
- **Model**: Gemini 2.0 Flash
- **Temperature**: 0.1 (high precision)
- **Tools**: None (pure LLM)
- **Responsibilities**:
  - Citation formatting (APA, MLA, Chicago, IEEE)
  - Source deduplication
  - Bibliography generation
  - Metadata validation

#### 4. Knowledge Graph Agent
- **Model**: Gemini 2.0 Flash
- **Temperature**: 0.4 (structured output)
- **Tools**: None (pure LLM)
- **Responsibilities**:
  - Entity extraction
  - Relationship identification
  - Graph structure generation
  - Confidence scoring

## Data Flow

### Research Request Flow

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant WebSocket
    participant API
    participant Orchestrator
    participant Agents
    participant State
    
    User->>UI: Submit Query
    UI->>WebSocket: Connect & Send
    WebSocket->>API: Validate Request
    API->>State: Create Task
    API->>Orchestrator: Process Query
    
    Orchestrator->>Orchestrator: Decompose Query
    
    loop For Each Subtask
        Orchestrator->>Agents: Delegate Task
        Agents->>VertexAI: Process with Gemini
        VertexAI-->>Agents: Return Results
        Agents-->>Orchestrator: Task Complete
        Orchestrator->>State: Update Progress
        State-->>WebSocket: Progress Event
        WebSocket-->>UI: Update Display
    end
    
    Orchestrator->>Orchestrator: Synthesize Results
    Orchestrator-->>API: Final Results
    API->>State: Save Results
    API-->>WebSocket: Complete Event
    WebSocket-->>UI: Display Results
```

### Real-time Update Flow

```mermaid
graph LR
    Agent[Agent Activity] --> Event[Event Generated]
    Event --> PubSub[Pub/Sub Channel]
    PubSub --> Dist[Distribution]
    
    Dist --> WS1[WebSocket 1]
    Dist --> WS2[WebSocket 2]
    Dist --> WS3[WebSocket N]
    
    WS1 --> UI1[User 1 UI]
    WS2 --> UI2[User 2 UI]
    WS3 --> UI3[User N UI]
```

## Security Architecture

### Authentication Flow

```mermaid
graph LR
    User[User] --> Login[Login Request]
    Login --> Validate[Validate Credentials]
    Validate --> JWT[Generate JWT]
    JWT --> Access[Access Token]
    JWT --> Refresh[Refresh Token]
    
    Access --> API[API Requests]
    API --> Verify[Verify Token]
    Verify --> Authorize[Check Permissions]
    Authorize --> Process[Process Request]
    
    Refresh --> Renew[Renew Tokens]
    Renew --> Access
```

### Security Layers

1. **Network Security**
   - HTTPS/WSS encryption
   - CORS configuration
   - Trusted host validation

2. **Authentication**
   - JWT with refresh tokens
   - OAuth2 integration
   - API key support

3. **Authorization**
   - Role-based access (Admin, User)
   - Resource-level permissions
   - Operation rate limiting

4. **Input Validation**
   - SQL injection prevention
   - XSS sanitization
   - Command injection blocking

5. **Rate Limiting**
   - Per-user limits
   - Per-operation limits
   - WebSocket connection limits

## Scalability Design

### Horizontal Scaling

```mermaid
graph TB
    LB[Cloud Load Balancer]
    
    subgraph "Cloud Run Instances"
        API1[API Instance 1]
        API2[API Instance 2]
        API3[API Instance N]
    end
    
    subgraph "Shared State"
        Redis[(Redis Cluster)]
        Firestore[(Firestore)]
    end
    
    subgraph "Agent Pool"
        ADK1[ADK Instance 1]
        ADK2[ADK Instance 2]
        ADK3[ADK Instance N]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> Redis
    API2 --> Redis
    API3 --> Redis
    
    API1 --> Firestore
    API2 --> Firestore
    API3 --> Firestore
    
    API1 --> ADK1
    API2 --> ADK2
    API3 --> ADK3
```

### Caching Strategy

1. **Redis Cache Layers**
   - Session state (TTL: 1 hour)
   - Research results (TTL: 24 hours)
   - User preferences (TTL: 7 days)
   - Rate limit counters (TTL: window-based)

2. **Firestore Persistence**
   - Research history
   - User profiles
   - Collaboration data
   - Analytics data

3. **CDN Caching**
   - Static assets
   - Demo query results
   - Public research data

## Performance Optimization

### Agent Optimization
- Parallel task execution
- Result streaming
- Intelligent caching
- Query deduplication

### Database Optimization
- Connection pooling
- Query optimization
- Index management
- Read replicas

### Network Optimization
- WebSocket compression
- HTTP/2 support
- Request batching
- CDN distribution

## Monitoring & Observability

### Metrics Collection

```yaml
System Metrics:
  - Request rate
  - Response time
  - Error rate
  - Cache hit rate
  - Active users

Agent Metrics:
  - Task completion time
  - Success rate
  - Token usage
  - Error frequency

Resource Metrics:
  - CPU utilization
  - Memory usage
  - Network I/O
  - Database connections
```

### Logging Strategy

```yaml
Log Levels:
  ERROR: System errors, failures
  WARNING: Performance issues, degradation
  INFO: Request handling, agent activity
  DEBUG: Detailed execution flow

Log Structure:
  - Timestamp
  - Request ID
  - User ID
  - Agent name
  - Operation
  - Duration
  - Status
  - Metadata
```

### Alerting Rules

```yaml
Critical Alerts:
  - Error rate > 5%
  - Response time > 10s
  - Agent failure
  - Database connection failure

Warning Alerts:
  - Error rate > 1%
  - Response time > 5s
  - High memory usage (>80%)
  - Rate limit exceeded
```

## Deployment Architecture

### CI/CD Pipeline

```mermaid
graph LR
    Code[Code Push] --> GitHub[GitHub]
    GitHub --> CloudBuild[Cloud Build]
    
    CloudBuild --> Test[Run Tests]
    Test --> Build[Build Images]
    Build --> Push[Push to Registry]
    Push --> Deploy[Deploy to Cloud Run]
    
    Deploy --> Staging[Staging Env]
    Staging --> Prod[Production]
```

### Environment Configuration

```yaml
Development:
  - Local Redis
  - Local PostgreSQL
  - Vertex AI dev project
  - Debug logging

Staging:
  - Cloud Redis
  - Cloud SQL
  - Vertex AI staging project
  - Info logging

Production:
  - Redis cluster
  - Cloud SQL HA
  - Vertex AI prod project
  - Error logging only
```

## Disaster Recovery

### Backup Strategy
- Database: Daily automated backups
- Firestore: Real-time replication
- Code: Git repository
- Secrets: Secret Manager versioning

### Recovery Procedures
1. Service failure: Auto-restart with Cloud Run
2. Database failure: Failover to replica
3. Region failure: Multi-region deployment
4. Complete failure: Restore from backups

## Future Architecture Considerations

### Planned Enhancements
1. **GraphQL API**: For more efficient data fetching
2. **Event Sourcing**: For complete audit trail
3. **Microservices**: Split monolith into services
4. **Kubernetes**: For more complex orchestration
5. **Multi-region**: Global distribution

### Scalability Roadmap
- Phase 1: Current architecture (1K users)
- Phase 2: Add read replicas (10K users)
- Phase 3: Microservices split (100K users)
- Phase 4: Global distribution (1M+ users)