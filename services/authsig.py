import hmac
import hashlib
import time
from typing import Optional

def compute_hmac(key: bytes, body: bytes) -> str:
    """Compute HMAC-SHA256 signature for request body."""
    signature = hmac.new(key, body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"

def verify_hmac_signature(
    key: bytes, 
    body: bytes, 
    signature_header: str, 
    server_id_header: str,
    body_server_id: str,
    max_clock_skew: int = 600  # 10 minutes
) -> tuple[bool, str]:
    """
    Verify HMAC signature and server ID consistency.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not key:
        return False, "No agent key configured"
    
    if not signature_header:
        return False, "Missing X-Signature header"
    
    if not signature_header.startswith("sha256="):
        return False, "Invalid signature format"
    
    if not server_id_header:
        return False, "Missing X-Server-ID header"
    
    # Verify server ID consistency
    if body_server_id != server_id_header:
        return False, "Server ID mismatch between header and body"
    
    # Extract signature from header
    expected_signature = signature_header
    
    # Compute actual signature
    actual_signature = compute_hmac(key, body)
    
    # Compare signatures (constant-time comparison)
    if not hmac.compare_digest(expected_signature, actual_signature):
        return False, "Invalid signature"
    
    return True, ""

def validate_timestamp(timestamp_str: str, max_skew: int = 600) -> tuple[bool, str]:
    """
    Validate timestamp for replay protection.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Parse ISO format timestamp
        from datetime import datetime
        import pytz
        
        # Parse the timestamp
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        # Convert to UTC timestamp
        utc_timestamp = dt.timestamp()
        current_time = time.time()
        
        # Check clock skew
        if abs(current_time - utc_timestamp) > max_skew:
            return False, f"Clock skew too large: {abs(current_time - utc_timestamp):.0f}s"
        
        return True, ""
        
    except (ValueError, TypeError) as e:
        return False, f"Invalid timestamp format: {str(e)}"
