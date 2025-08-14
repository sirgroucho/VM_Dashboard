import os
import json
import html
from datetime import datetime, timedelta
from typing import Optional
from flask import Blueprint, render_template, request, jsonify, Response, session, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import Session

from models import LogEvent, get_db, SessionLocal
from services.authsig import verify_hmac_signature, validate_timestamp
from services.logbus import log_event_bus
from decorators import require_perm

logs_bp = Blueprint('logs', __name__)

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configuration
AGENT_KEY = os.getenv('AGENT_KEY', '').encode()
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '30'))

# Role checking function removed - now using permission decorators

def sanitize_message(message: str) -> str:
    """Sanitize message to prevent HTML injection."""
    return html.escape(message.strip())

def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse datetime string from query parameters."""
    if not date_str:
        return None
    
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try common formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except:
            pass
    
    return None

@logs_bp.route("/logs")
@require_perm("logs:view")
def logs_page():
    """Logs page with filters and table."""
    
    # Get available servers and event types for dropdowns
    db = SessionLocal()
    try:
        servers = db.query(LogEvent.server_id).distinct().all()
        event_types = db.query(LogEvent.event_type).distinct().all()
        severities = ['DEBUG', 'INFO', 'WARN', 'ERROR']
        
        servers = [s[0] for s in servers if s[0]]
        event_types = [e[0] for e in event_types if e[0]]
    finally:
        db.close()
    
    return render_template('logs.html', 
                         servers=servers, 
                         event_types=event_types, 
                         severities=severities)

@logs_bp.route("/api/logs")
@require_perm("logs:view")
def get_logs():
    """Get logs with filtering and pagination."""
    
    # Parse query parameters
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(200, max(1, int(request.args.get('page_size', 50))))
    
    # Filters
    server_id = request.args.get('server_id')
    event_type = request.args.get('event_type')
    severity = request.args.get('severity')
    search_query = request.args.get('q', '').strip()
    since = request.args.get('since')
    until = request.args.get('until')
    
    # Parse dates
    since_dt = parse_datetime(since) if since else None
    until_dt = parse_datetime(until) if until else None
    
    # Build query
    db = SessionLocal()
    try:
        query = db.query(LogEvent)
        
        # Apply filters
        if server_id:
            query = query.filter(LogEvent.server_id == server_id)
        if event_type:
            query = query.filter(LogEvent.event_type == event_type)
        if severity:
            query = query.filter(LogEvent.severity == severity)
        if search_query:
            query = query.filter(LogEvent.message.ilike(f'%{search_query}%'))
        if since_dt:
            query = query.filter(LogEvent.ts >= since_dt)
        if until_dt:
            query = query.filter(LogEvent.ts <= until_dt)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        query = query.order_by(desc(LogEvent.ts), desc(LogEvent.id))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute query
        logs = query.all()
        
        # Convert to dict
        items = [log.to_dict() for log in logs]
        
        return jsonify({
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": (page * page_size) < total
        })
        
    finally:
        db.close()

@logs_bp.route("/api/logs/<int:log_id>")
@require_perm("logs:view")
def get_log(log_id: int):
    """Get a single log entry by ID."""
    
    db = SessionLocal()
    try:
        log = db.query(LogEvent).filter(LogEvent.id == log_id).first()
        if not log:
            return jsonify({"error": "Log not found"}), 404
        
        return jsonify(log.to_dict())
    finally:
        db.close()

@logs_bp.route("/api/ingest/logs", methods=["POST"])
@limiter.limit("60 per minute")
def ingest_logs():
    """Ingest logs from agents with HMAC authentication."""
    # Check content type
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    # Get headers
    signature = request.headers.get('X-Signature', '')
    server_id_header = request.headers.get('X-Server-ID', '')
    
    if not signature or not server_id_header:
        return jsonify({"error": "Missing X-Signature or X-Server-ID header"}), 401
    
    # Get raw body
    body = request.get_data()
    
    # Parse JSON
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # Handle both single object and array
    if isinstance(data, dict):
        logs_data = [data]
    elif isinstance(data, list):
        logs_data = data
    else:
        return jsonify({"error": "Data must be object or array"}), 400
    
    # Validate each log entry
    validated_logs = []
    for log_data in logs_data:
        # Required fields
        required_fields = ['server_id', 'host', 'source', 'event_type', 'severity', 'message']
        for field in required_fields:
            if field not in log_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate server_id consistency
        if log_data['server_id'] != server_id_header:
            return jsonify({"error": "Server ID mismatch"}), 400
        
        # Validate severity
        if log_data['severity'] not in ['DEBUG', 'INFO', 'WARN', 'ERROR']:
            return jsonify({"error": f"Invalid severity: {log_data['severity']}"}), 400
        
        # Sanitize message
        log_data['message'] = sanitize_message(log_data['message'])
        
        # Parse timestamp
        if 'ts' in log_data:
            timestamp_valid, timestamp_error = validate_timestamp(log_data['ts'])
            if not timestamp_valid:
                return jsonify({"error": f"Invalid timestamp: {timestamp_error}"}), 400
            try:
                if log_data['ts'].endswith('Z'):
                    log_data['ts'] = log_data['ts'][:-1] + '+00:00'
                log_data['ts'] = datetime.fromisoformat(log_data['ts'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid timestamp format"}), 400
        else:
            log_data['ts'] = datetime.utcnow()
        
        # Validate metadata (must be dict if present)
        if 'metadata' in log_data and not isinstance(log_data['metadata'], dict):
            return jsonify({"error": "Metadata must be a dictionary"}), 400
        
        validated_logs.append(log_data)
    
    # Verify HMAC signature
    is_valid, error_msg = verify_hmac_signature(
        AGENT_KEY, body, signature, server_id_header, validated_logs[0]['server_id']
    )
    
    if not is_valid:
        return jsonify({"error": error_msg}), 401
    
    # Insert logs into database
    db = SessionLocal()
    try:
        inserted_count = 0
        for log_data in validated_logs:
            log_event = LogEvent(**log_data)
            db.add(log_event)
            inserted_count += 1
        
        db.commit()
        
        # Publish to SSE
        for log_data in validated_logs:
            log_event_dict = {
                'id': None,  # Will be set by the database
                'server_id': log_data['server_id'],
                'host': log_data['host'],
                'source': log_data['source'],
                'event_type': log_data['event_type'],
                'severity': log_data['severity'],
                'message': log_data['message'],
                'metadata': log_data.get('metadata'),
                'ts': log_data['ts'].isoformat() + 'Z'
            }
            log_event_bus.publish(log_event_dict)
        
        return jsonify({"ok": True, "inserted": inserted_count})
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        db.close()

@logs_bp.route("/stream/logs")
@require_perm("logs:stream")
def stream_logs():
    """Server-Sent Events stream for real-time logs."""
    
    # Get filters from query params
    filters = {}
    for param in ['server_id', 'event_type', 'severity']:
        value = request.args.get(param)
        if value:
            filters[param] = value
    
    def generate():
        # Create unique client ID
        client_id = f"{session.get('username', 'unknown')}_{int(datetime.utcnow().timestamp())}"
        
        # Create SSE client
        from services.logbus import sse_manager
        client = sse_manager.create_client(client_id, filters)
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id})}\n\n"
            
            # Send heartbeat every 30 seconds
            last_heartbeat = datetime.utcnow()
            
            while True:
                # Check for new events
                event = client.get_event(timeout=30.0)
                if event:
                    yield f"data: {json.dumps(event)}\n\n"
                
                # Send heartbeat
                now = datetime.utcnow()
                if (now - last_heartbeat).total_seconds() >= 30:
                    yield f": heartbeat {now.isoformat()}\n\n"
                    last_heartbeat = now
                    
        except GeneratorExit:
            # Client disconnected
            pass
        finally:
            # Cleanup
            sse_manager.remove_client(client_id)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )

@logs_bp.route("/api/logs/stats")
@require_perm("logs:view")
def get_log_stats():
    """Get log statistics for dashboard."""
    
    db = SessionLocal()
    try:
        # Total logs
        total_logs = db.query(LogEvent).count()
        
        # Logs by severity
        severity_counts = db.query(
            LogEvent.severity, 
            db.func.count(LogEvent.id)
        ).group_by(LogEvent.severity).all()
        
        # Logs by server
        server_counts = db.query(
            LogEvent.server_id, 
            db.func.count(LogEvent.id)
        ).group_by(LogEvent.server_id).all()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_logs = db.query(LogEvent).filter(LogEvent.ts >= yesterday).count()
        
        return jsonify({
            "total_logs": total_logs,
            "recent_logs": recent_logs,
            "severity_counts": dict(severity_counts),
            "server_counts": dict(server_counts)
        })
        
    finally:
        db.close()
