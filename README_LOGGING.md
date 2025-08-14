# Marx-Tec VM Dashboard - Logging System

## Quick Start

The logging system provides secure, real-time log ingestion and viewing for your homelab Minecraft platform.

### 1. Setup

```bash
# Install dependencies
make install

# Initialize database
make db-init

# Set your agent key in secrets/secret.env
# Edit AGENT_KEY=your_secure_key_here

# Start the dashboard
make run
```

### 2. Test the System

```bash
# Send test logs (replace YOUR_KEY with your actual agent key)
python scripts/send_fake_logs.py --agent-key YOUR_KEY --count 10
```

### 3. View Logs

- Navigate to `/logs` in your browser
- Login with appropriate credentials (mcrole: viewer or admin)
- Use filters to search logs
- Toggle "Live Updates" for real-time streaming

## Features

✅ **Secure Ingestion**: HMAC-SHA256 authentication for agents  
✅ **Real-time Updates**: Server-Sent Events (SSE) streaming  
✅ **Advanced Filtering**: Date, server, type, severity, text search  
✅ **Role-based Access**: Viewer/Admin permissions  
✅ **Automatic Retention**: Configurable log cleanup  
✅ **Performance Optimized**: Indexed database queries  
✅ **Production Ready**: Rate limiting, input validation, error handling  

## API Endpoints

| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/logs` | GET | Logs dashboard UI |
| `/api/ingest/logs` | POST | Ingest logs from agents |
| `/api/logs` | GET | Query logs with filters |
| `/api/logs/<id>` | GET | Get single log entry |
| `/stream/logs` | GET | Real-time SSE stream |

## Configuration

### Environment Variables

```bash
# Database (SQLite or PostgreSQL)
DATABASE_URL=sqlite:///data/app.db

# Agent authentication key
AGENT_KEY=your_secure_agent_key_here

# Log retention period (days)
LOG_RETENTION_DAYS=30
```

### Agent Integration

```python
import requests
import hmac
import hashlib
import json

def send_log(dashboard_url, agent_key, server_id, event_type, severity, message, metadata=None):
    log_data = {
        "server_id": server_id,
        "host": "127.0.0.1",
        "source": "agent",
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "metadata": metadata or {}
    }
    
    body = json.dumps(log_data)
    signature = hmac.new(
        agent_key.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Signature": f"sha256={signature}",
        "X-Server-ID": server_id
    }
    
    response = requests.post(
        f"{dashboard_url}/api/ingest/logs",
        data=body,
        headers=headers
    )
    
    return response.json()

# Usage
send_log(
    "http://localhost:5000",
    "your_key",
    "server-01",
    "player_join",
    "INFO",
    "Player alice joined",
    {"player": "alice", "ip": "192.168.1.100"}
)
```

## Docker Deployment

```bash
# Build and start
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

## Security

- **HMAC Authentication**: All agent requests must be signed
- **Rate Limiting**: 60 requests/minute per server
- **Input Validation**: All inputs sanitized and validated
- **RBAC**: Role-based access control for users
- **HTTPS**: Use behind nginx with TLS in production

## Troubleshooting

### Common Issues

1. **"No agent key configured"**
   - Set `AGENT_KEY` in `secrets/secret.env`

2. **"Invalid signature"**
   - Verify your agent key matches the dashboard
   - Check signature computation

3. **Database errors**
   - Run `make db-init` to create tables
   - Check disk space and permissions

4. **SSE not working**
   - Ensure nginx is configured for SSE
   - Check browser console for errors

### Debug Mode

```bash
export FLASK_ENV=development
python app.py
```

## Performance Tips

- **Database Indexes**: Automatically created for optimal queries
- **Pagination**: Default 50 items per page, max 200
- **SSE Filtering**: Server-side filtering reduces bandwidth
- **Connection Limits**: Automatic cleanup of dead connections

## Monitoring

The system includes:
- Automatic log retention (configurable)
- Connection monitoring
- Error tracking and logging
- Performance metrics

## Support

For issues and questions:
1. Check the logs in your browser console
2. Review the comprehensive documentation in `docs/logging.md`
3. Check the Flask application logs

## Next Steps

- [ ] Set up monitoring and alerting
- [ ] Configure log rotation and compression
- [ ] Implement advanced analytics
- [ ] Add log export functionality
- [ ] Set up automated backups
