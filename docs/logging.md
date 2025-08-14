# Logging System Documentation

## Overview

The Marx-Tec VM Dashboard includes a comprehensive logging system that provides:
- Secure log ingestion from agents via HMAC authentication
- Real-time log streaming via Server-Sent Events (SSE)
- Advanced filtering and search capabilities
- Automatic log retention and cleanup
- Role-based access control

## Architecture

### Components

1. **Database Layer**: SQLite/PostgreSQL with SQLAlchemy ORM
2. **API Layer**: RESTful endpoints for ingestion and querying
3. **SSE Layer**: Real-time event streaming
4. **Retention Service**: Automatic cleanup of old logs
5. **Authentication**: HMAC-SHA256 for agents, session-based for users

### Database Schema

```sql
CREATE TABLE log_events (
    id BIGINT PRIMARY KEY AUTOINCREMENT,
    server_id TEXT NOT NULL,
    host TEXT NOT NULL,
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSON,
    ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `(ts DESC)` - Primary pagination index
- `(server_id, ts)` - Server-specific queries
- `(event_type, ts)` - Event type filtering
- `(severity, ts)` - Severity filtering
- Individual indexes on all filterable fields

## API Reference

### Log Ingestion

**Endpoint:** `POST /api/ingest/logs`

**Headers Required:**
- `Content-Type: application/json`
- `X-Signature: sha256=<hmac_hex>`
- `X-Server-ID: <server_id>`

**Request Body:**
```json
{
  "server_id": "beelink-01",
  "host": "127.0.0.1",
  "source": "agent",
  "event_type": "player_join",
  "severity": "INFO",
  "message": "Player jon joined",
  "metadata": {"player": "jon", "ip": "10.0.0.5"},
  "ts": "2025-08-11T23:59:59Z"
}
```

**Batch Ingestion:**
```json
[
  { /* log entry 1 */ },
  { /* log entry 2 */ }
]
```

**Response:**
```json
{
  "ok": true,
  "inserted": 1
}
```

### Log Querying

**Endpoint:** `GET /api/logs`

**Query Parameters:**
- `page` (default: 1) - Page number
- `page_size` (default: 50, max: 200) - Items per page
- `server_id` - Filter by server
- `event_type` - Filter by event type
- `severity` - Filter by severity
- `q` - Search in message content
- `since` - Start date (ISO format)
- `until` - End date (ISO format)

**Response:**
```json
{
  "items": [
    {
      "id": 123,
      "server_id": "beelink-01",
      "host": "127.0.0.1",
      "source": "agent",
      "event_type": "player_join",
      "severity": "INFO",
      "message": "Player jon joined",
      "metadata": {"player": "jon", "ip": "10.0.0.5"},
      "ts": "2025-08-11T23:59:59Z"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total": 150,
  "has_next": true
}
```

### Individual Log

**Endpoint:** `GET /api/logs/<id>`

**Response:** Single log entry object

### Real-time Streaming

**Endpoint:** `GET /stream/logs`

**Query Parameters:** Same as log querying for filtering

**Response:** Server-Sent Events stream

**Event Format:**
```
data: {"id": 123, "server_id": "beelink-01", ...}

: heartbeat 2025-08-11T23:59:59Z
```

## HMAC Authentication

### Signature Computation

```python
import hmac
import hashlib

def compute_signature(key: str, body: bytes) -> str:
    signature = hmac.new(
        key.encode(), 
        body, 
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"
```

### Example with curl

```bash
# Generate signature
BODY='{"server_id":"test","host":"127.0.0.1","source":"agent","event_type":"test","severity":"INFO","message":"test"}'
SIGNATURE=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "your_agent_key" | sed 's/^.*= //')

# Send request
curl -X POST http://localhost:5000/api/ingest/logs \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=$SIGNATURE" \
  -H "X-Server-ID: test" \
  -d "$BODY"
```

### Security Features

- **HMAC-SHA256**: Cryptographically secure signatures
- **Server ID Validation**: Header must match body server_id
- **Rate Limiting**: 60 requests/minute per server
- **Input Validation**: All fields validated and sanitized
- **Clock Skew Protection**: Optional timestamp validation

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///data/app.db
# or
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Agent authentication
AGENT_KEY=your_secure_agent_key_here

# Log retention
LOG_RETENTION_DAYS=30
```

### Docker Compose

```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./secrets:/app/secrets
    environment:
      - DATABASE_URL=sqlite:///data/app.db
      - AGENT_KEY=${AGENT_KEY}
      - LOG_RETENTION_DAYS=30
```

## Usage Examples

### Python Agent

```python
import requests
import hmac
import hashlib
import json

class LogAgent:
    def __init__(self, dashboard_url: str, agent_key: str, server_id: str):
        self.dashboard_url = dashboard_url
        self.agent_key = agent_key
        self.server_id = server_id
    
    def send_log(self, event_type: str, severity: str, message: str, metadata: dict = None):
        log_data = {
            "server_id": self.server_id,
            "host": "127.0.0.1",
            "source": "agent",
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "metadata": metadata or {}
        }
        
        body = json.dumps(log_data)
        signature = hmac.new(
            self.agent_key.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-Signature": f"sha256={signature}",
            "X-Server-ID": self.server_id
        }
        
        response = requests.post(
            f"{self.dashboard_url}/api/ingest/logs",
            data=body,
            headers=headers
        )
        
        return response.json()

# Usage
agent = LogAgent("http://localhost:5000", "your_key", "server-01")
agent.send_log("player_join", "INFO", "Player joined", {"player": "alice"})
```

### JavaScript Client

```javascript
// Connect to SSE stream
const eventSource = new EventSource('/stream/logs?server_id=server-01');

eventSource.onmessage = function(event) {
    const log = JSON.parse(event.data);
    console.log('New log:', log);
    
    // Add to UI
    addLogToTable(log);
};

// Send logs via API
async function sendLog(logData) {
    const response = await fetch('/api/ingest/logs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Signature': computeHMAC(logData),
            'X-Server-ID': logData.server_id
        },
        body: JSON.stringify(logData)
    });
    
    return response.json();
}
```

## Testing

### Test Script

Use the included test script to send fake logs:

```bash
# Install dependencies
pip install requests

# Send 10 test logs
python scripts/send_fake_logs.py \
  --count 10 \
  --server-id test-server \
  --url http://localhost:5000 \
  --agent-key your_key

# Send logs with delay
python scripts/send_fake_logs.py \
  --count 100 \
  --delay 0.5 \
  --agent-key your_key
```

### Manual Testing

1. **Start the dashboard:**
   ```bash
   python app.py
   ```

2. **Initialize database:**
   ```bash
   python scripts/db_init.py
   ```

3. **Send test logs:**
   ```bash
   python scripts/send_fake_logs.py --agent-key test_key
   ```

4. **View logs in browser:**
   - Navigate to `/logs`
   - Login with appropriate credentials
   - Toggle live updates to see real-time logs

## Performance Considerations

### Database Optimization

- **Indexes**: All filterable fields are indexed
- **Pagination**: Uses LIMIT/OFFSET with ORDER BY ts DESC
- **Bulk Inserts**: Batch ingestion supported
- **Connection Pooling**: SQLAlchemy session management

### SSE Optimization

- **Filtering**: Server-side filtering reduces unnecessary events
- **Queue Management**: Client-side queues prevent memory issues
- **Heartbeats**: Regular keep-alive messages
- **Connection Limits**: Automatic cleanup of dead connections

### Rate Limiting

- **Per-Server Limits**: 60 requests/minute per server_id
- **Global Limits**: 200/day, 50/hour per IP
- **Configurable**: Easy to adjust limits in code

## Monitoring and Maintenance

### Retention Service

- **Automatic Cleanup**: Runs every 24 hours
- **Configurable Period**: Set via LOG_RETENTION_DAYS
- **Manual Trigger**: Available via API
- **Statistics**: Retention metrics available

### Health Checks

- **Database Connectivity**: Automatic reconnection
- **SSE Health**: Connection monitoring
- **Error Logging**: Comprehensive error tracking

### Backup Recommendations

- **Database Backups**: Regular SQLite/PostgreSQL backups
- **Log Rotation**: Consider log rotation for high-volume systems
- **Monitoring**: Monitor disk usage and performance

## Troubleshooting

### Common Issues

1. **HMAC Validation Failed**
   - Check AGENT_KEY environment variable
   - Verify signature computation
   - Ensure server_id consistency

2. **Database Connection Errors**
   - Check DATABASE_URL format
   - Verify database permissions
   - Check disk space

3. **SSE Connection Issues**
   - Check nginx configuration for SSE
   - Verify client-side EventSource support
   - Check browser console for errors

4. **Performance Issues**
   - Review database indexes
   - Check query performance
   - Monitor memory usage

### Debug Mode

Enable debug mode for detailed logging:

```bash
export FLASK_ENV=development
python app.py
```

### Log Analysis

Use the dashboard's built-in filtering and search to analyze logs:

- **Time-based Analysis**: Use date filters for trend analysis
- **Error Tracking**: Filter by severity to track issues
- **Server Monitoring**: Filter by server_id for individual server analysis
- **Pattern Recognition**: Use search to find specific patterns

## Security Best Practices

1. **Strong Agent Keys**: Use cryptographically secure random keys
2. **Network Security**: Use HTTPS in production
3. **Access Control**: Implement proper RBAC
4. **Input Validation**: All inputs are validated and sanitized
5. **Rate Limiting**: Prevent abuse and DoS attacks
6. **Audit Logging**: Track all access and changes

## Future Enhancements

- **Advanced Analytics**: Log aggregation and reporting
- **Alerting**: Configurable alerts for specific conditions
- **Export**: Log export in various formats
- **Compression**: Automatic log compression for storage
- **Multi-tenancy**: Support for multiple organizations
- **API Versioning**: Versioned API endpoints
