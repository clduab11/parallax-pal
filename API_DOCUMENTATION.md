# 📚 Parallax Pal API Documentation

## Overview

The Parallax Pal API provides programmatic access to our multi-agent research platform. This RESTful API supports real-time WebSocket connections for live research updates.

**Base URL**: `https://api.parallaxpal.app`  
**WebSocket URL**: `wss://api.parallaxpal.app/ws`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Obtaining Tokens

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "subscription_tier": "pro"
  }
}
```

### Refreshing Tokens

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Rate Limiting

API rate limits vary by subscription tier:

| Tier       | Requests/Hour | Concurrent Connections | Query Limit/Hour |
|------------|---------------|------------------------|------------------|
| Free       | 60            | 2                      | 10               |
| Basic      | 300           | 5                      | 50               |
| Pro        | 1000          | 10                     | 200              |
| Enterprise | 5000          | 50                     | 1000             |

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Core Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "api": "healthy",
    "websocket": "healthy",
    "state_manager": "healthy",
    "rate_limiter": "healthy",
    "adk_agents": "healthy"
  },
  "timestamp": "2025-01-15T10:00:00Z"
}
```

### Research Endpoints

#### Create Research Task

```http
POST /api/adk/research
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "What are the latest breakthroughs in quantum computing?",
  "mode": "comprehensive",
  "focus_areas": ["hardware", "algorithms", "applications"],
  "language": "en"
}
```

**Parameters:**
- `query` (required): Research question (3-1000 characters)
- `mode` (optional): Research mode - "quick", "comprehensive", "continuous" (default: "comprehensive")
- `focus_areas` (optional): Array of focus areas (max 10)
- `language` (optional): Two-letter language code (default: "en")

**Response:**
```json
{
  "task_id": "task_20250115_100000_user123",
  "status": "created",
  "estimated_time": 30,
  "websocket_url": "wss://api.parallaxpal.app/ws",
  "message": "Connect to WebSocket for real-time updates"
}
```

#### Get Research Status

```http
GET /api/adk/research/{task_id}/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "task_id": "task_20250115_100000_user123",
  "status": "in_progress",
  "progress": 65,
  "current_agent": "analysis",
  "agents_completed": ["orchestrator", "retrieval"],
  "estimated_remaining": 15
}
```

#### Get Research Results

```http
GET /api/adk/research/{task_id}/results
Authorization: Bearer <token>
```

**Response:**
```json
{
  "task_id": "task_20250115_100000_user123",
  "status": "completed",
  "query": "What are the latest breakthroughs in quantum computing?",
  "summary": "Recent breakthroughs in quantum computing...",
  "findings": [
    "Quantum error correction improved by 50%",
    "Room-temperature quantum operations achieved"
  ],
  "sources": [
    {
      "title": "Nature: Quantum Computing Advances",
      "url": "https://nature.com/quantum-2025",
      "reliability": 0.95,
      "summary": "Detailed research on quantum error correction..."
    }
  ],
  "citations": {
    "apa": ["Author, A. (2025). Title. Nature, 123, 45-67."],
    "mla": ["Author, Alice. \"Title.\" Nature, vol. 123, 2025, pp. 45-67."],
    "chicago": ["Author, Alice. \"Title.\" Nature 123 (2025): 45-67."]
  },
  "knowledge_graph": {
    "nodes": [
      {
        "id": "1",
        "label": "Quantum Computing",
        "type": "concept",
        "properties": {
          "definition": "Computing using quantum phenomena"
        }
      }
    ],
    "edges": [
      {
        "source": "1",
        "target": "2",
        "type": "requires",
        "weight": 0.9
      }
    ]
  },
  "follow_up_questions": [
    "How do topological qubits work?",
    "What are the practical applications?"
  ],
  "metadata": {
    "duration_seconds": 28.5,
    "tokens_used": 15420,
    "sources_analyzed": 23,
    "confidence_score": 0.92
  }
}
```

### Voice Interaction

#### Transcribe Audio

```http
POST /api/voice/transcribe
Authorization: Bearer <token>
Content-Type: multipart/form-data

audio_file: <binary audio data>
```

**Supported formats**: webm, wav, mp3, ogg

**Response:**
```json
{
  "success": true,
  "transcript": "What are the latest breakthroughs in quantum computing?",
  "confidence": 0.95,
  "language": "en-US",
  "word_timings": [
    {
      "word": "What",
      "start_time": 0.0,
      "end_time": 0.3
    }
  ],
  "is_final": true
}
```

#### Text-to-Speech

```http
POST /api/voice/synthesize
Authorization: Bearer <token>
Content-Type: application/json

{
  "text": "Here are the latest quantum computing breakthroughs",
  "emotion": "default",
  "format": "mp3"
}
```

**Parameters:**
- `emotion`: "default", "excited", "thoughtful"
- `format`: "mp3", "wav", "ogg"

**Response:**
```json
{
  "success": true,
  "audio_data": "base64-encoded-audio...",
  "format": "mp3",
  "duration_seconds": 4.2,
  "voice": "en-US-Neural2-F"
}
```

### Collaboration

#### Create Collaboration

```http
POST /api/collaboration/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Quantum Computing Research Team",
  "description": "Collaborative research on quantum breakthroughs",
  "settings": {
    "max_members": 10,
    "require_approval": false,
    "share_mode": "private"
  }
}
```

**Response:**
```json
{
  "collaboration_id": "collab_a1b2c3d4e5",
  "status": "created",
  "invite_code": "QC2025RESEARCH",
  "owner_id": "user_123"
}
```

#### Join Collaboration

```http
POST /api/collaboration/{collab_id}/join
Authorization: Bearer <token>
Content-Type: application/json

{
  "invite_code": "QC2025RESEARCH"
}
```

#### Share Research

```http
POST /api/collaboration/{collab_id}/share
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_id": "task_20250115_100000_user123",
  "include_graph": true,
  "message": "Found some interesting quantum computing insights"
}
```

### Export

#### Export Research

```http
POST /api/export
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_id": "task_20250115_100000_user123",
  "format": "pdf",
  "template": "academic",
  "options": {
    "include_graph": true,
    "include_citations": true,
    "page_size": "letter"
  }
}
```

**Supported formats by tier:**
- **Free**: txt, json
- **Basic**: txt, json, pdf
- **Pro**: txt, json, pdf, docx, notion
- **Enterprise**: All formats + custom

**Response:**
```json
{
  "success": true,
  "format": "pdf",
  "filename": "research_report_20250115_100000.pdf",
  "data": "base64-encoded-file-content...",
  "size": 245632
}
```

### System Metrics (Admin Only)

```http
GET /api/admin/metrics
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "active_connections": 42,
  "total_users": 1523,
  "active_research_tasks": 18,
  "agent_health": {
    "overall_status": "healthy",
    "agents": {
      "orchestrator": {
        "status": "healthy",
        "response_time_seconds": 0.8
      }
    }
  },
  "requests_today": {
    "20250115": 3420
  }
}
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('wss://api.parallaxpal.app/ws');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your-jwt-token'
  }));
};
```

### Message Types

#### Research Query

```json
{
  "type": "research_query",
  "data": {
    "query": "What are quantum computing applications?",
    "mode": "comprehensive",
    "focus_areas": ["healthcare", "cryptography"]
  }
}
```

#### Progress Updates

```json
{
  "type": "research_update",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "task_20250115_100000_user123",
  "agent": "retrieval",
  "progress": 30,
  "message": "Found 15 relevant sources"
}
```

#### Research Complete

```json
{
  "type": "research_completed",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "task_20250115_100000_user123",
  "results": {
    "summary": "...",
    "findings": [...],
    "sources": [...],
    "knowledge_graph": {...}
  }
}
```

### Error Handling

```json
{
  "type": "error",
  "code": "rate_limited",
  "error": "Too many requests. Please try again later.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `auth_failed` | 401 | Authentication failed |
| `auth_expired` | 401 | Token expired |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `invalid_input` | 400 | Invalid request data |
| `rate_limited` | 429 | Rate limit exceeded |
| `quota_exceeded` | 402 | Usage quota exceeded |
| `server_error` | 500 | Internal server error |

## SDK Examples

### Python

```python
import requests
import websocket
import json

class ParallaxPalClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.parallaxpal.app"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def research(self, query, mode="comprehensive"):
        response = requests.post(
            f"{self.base_url}/api/adk/research",
            headers=self.headers,
            json={"query": query, "mode": mode}
        )
        return response.json()
    
    def connect_websocket(self, on_message):
        ws = websocket.WebSocketApp(
            "wss://api.parallaxpal.app/ws",
            on_message=on_message,
            on_open=lambda ws: ws.send(json.dumps({
                "type": "auth",
                "token": self.api_key
            }))
        )
        ws.run_forever()

# Usage
client = ParallaxPalClient("your-api-key")
result = client.research("Latest AI breakthroughs")
print(result["task_id"])
```

### JavaScript/TypeScript

```typescript
class ParallaxPalClient {
  private apiKey: string;
  private baseUrl = 'https://api.parallaxpal.app';
  private ws: WebSocket | null = null;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async research(query: string, mode = 'comprehensive'): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/adk/research`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query, mode })
    });
    return response.json();
  }

  connectWebSocket(onMessage: (data: any) => void): void {
    this.ws = new WebSocket('wss://api.parallaxpal.app/ws');
    
    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify({
        type: 'auth',
        token: this.apiKey
      }));
    };
    
    this.ws.onmessage = (event) => {
      onMessage(JSON.parse(event.data));
    };
  }
}

// Usage
const client = new ParallaxPalClient('your-api-key');
const result = await client.research('Latest AI breakthroughs');
console.log(result.task_id);
```

### cURL Examples

```bash
# Login
curl -X POST https://api.parallaxpal.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Create research task
curl -X POST https://api.parallaxpal.app/api/adk/research \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"query":"Quantum computing breakthroughs","mode":"comprehensive"}'

# Export results
curl -X POST https://api.parallaxpal.app/api/export \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"task_id":"task_123","format":"pdf"}' \
  -o research_report.pdf
```

## Best Practices

1. **Authentication**
   - Store tokens securely
   - Refresh tokens before expiry
   - Never expose tokens in client-side code

2. **Rate Limiting**
   - Implement exponential backoff
   - Cache results when possible
   - Use WebSocket for real-time needs

3. **Error Handling**
   - Always check response status
   - Handle network timeouts
   - Provide user-friendly error messages

4. **Performance**
   - Use appropriate research modes
   - Batch requests when possible
   - Close WebSocket connections when done

5. **Security**
   - Validate all inputs
   - Use HTTPS/WSS only
   - Keep SDKs updated

## Changelog

### v2.0.0 (2025-01-15)
- Native ADK integration
- Voice interaction support
- Collaborative research
- Enhanced export formats
- Performance metrics API

### v1.0.0 (2024-12-01)
- Initial API release
- Basic research functionality
- WebSocket support