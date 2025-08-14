#!/usr/bin/env python3
"""
Test script for sending fake log events to the dashboard.
Usage: python scripts/send_fake_logs.py [--count N] [--server-id SERVER] [--url URL]
"""

import argparse
import json
import random
import time
import hmac
import hashlib
import requests
from datetime import datetime, timedelta

def compute_hmac(key: str, body: bytes) -> str:
    """Compute HMAC-SHA256 signature for request body."""
    signature = hmac.new(key.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"

def generate_fake_log(server_id: str) -> dict:
    """Generate a fake log event."""
    event_types = [
        'player_join', 'player_leave', 'console', 'crash', 
        'heartbeat', 'metric', 'backup', 'restart', 'plugin_load'
    ]
    
    severities = ['DEBUG', 'INFO', 'WARN', 'ERROR']
    
    sources = ['mc_server', 'agent', 'dashboard', 'backup_service']
    
    messages = [
        "Player {player} joined the server",
        "Player {player} left the server",
        "Server backup completed successfully",
        "Plugin {plugin} loaded successfully",
        "Server restart scheduled for {time}",
        "Memory usage: {memory}MB",
        "CPU usage: {cpu}%",
        "Network traffic: {bytes} bytes/s",
        "World save completed",
        "New player registered: {player}"
    ]
    
    # Generate random data
    event_type = random.choice(event_types)
    severity = random.choice(severities)
    source = random.choice(sources)
    message_template = random.choice(messages)
    
    # Fill in message template
    if '{player}' in message_template:
        players = ['alice', 'bob', 'charlie', 'diana', 'eve', 'frank', 'grace']
        message = message_template.format(player=random.choice(players))
    elif '{plugin}' in message_template:
        plugins = ['WorldEdit', 'Essentials', 'LuckPerms', 'CoreProtect', 'WorldGuard']
        message = message_template.format(plugin=random.choice(plugins))
    elif '{time}' in message_template:
        future_time = datetime.utcnow() + timedelta(hours=random.randint(1, 24))
        message = message_template.format(time=future_time.strftime('%H:%M'))
    elif '{memory}' in message_template:
        message = message_template.format(memory=random.randint(512, 8192))
    elif '{cpu}' in message_template:
        message = message_template.format(cpu=random.randint(5, 95))
    elif '{bytes}' in message_template:
        message = message_template.format(bytes=random.randint(1000, 1000000))
    else:
        message = message_template
    
    # Generate metadata
    metadata = {}
    if event_type in ['player_join', 'player_leave']:
        metadata = {
            'player': random.choice(['alice', 'bob', 'charlie', 'diana', 'eve']),
            'ip': f"192.168.1.{random.randint(1, 254)}",
            'uuid': f"uuid-{random.randint(1000000, 9999999)}"
        }
    elif event_type == 'metric':
        metadata = {
            'memory_used': random.randint(512, 8192),
            'cpu_usage': random.randint(5, 95),
            'players_online': random.randint(0, 20),
            'tps': random.uniform(15.0, 20.0)
        }
    elif event_type == 'backup':
        metadata = {
            'size_mb': random.randint(100, 5000),
            'duration_seconds': random.randint(30, 300),
            'worlds': random.choice(['world', 'world_nether', 'world_the_end'])
        }
    
    return {
        "server_id": server_id,
        "host": f"192.168.1.{random.randint(1, 254)}",
        "source": source,
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "metadata": metadata,
        "ts": datetime.utcnow().isoformat() + "Z"
    }

def send_logs(url: str, agent_key: str, server_id: str, count: int, delay: float):
    """Send fake logs to the dashboard."""
    print(f"Sending {count} fake logs to {url}")
    print(f"Server ID: {server_id}")
    print(f"Delay between requests: {delay}s")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    
    for i in range(count):
        # Generate fake log
        log_data = generate_fake_log(server_id)
        
        # Convert to JSON
        body = json.dumps(log_data, separators=(',', ':'))
        
        # Compute HMAC signature
        signature = compute_hmac(agent_key, body.encode())
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-Signature': signature,
            'X-Server-ID': server_id
        }
        
        try:
            # Send request
            response = requests.post(
                f"{url}/api/ingest/logs",
                data=body,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"[{i+1:3d}] ✓ Success: {result.get('inserted', 1)} log(s) inserted")
                success_count += 1
            else:
                print(f"[{i+1:3d}] ✗ Error {response.status_code}: {response.text}")
                error_count += 1
                
        except requests.exceptions.RequestException as e:
            print(f"[{i+1:3d}] ✗ Request failed: {e}")
            error_count += 1
        
        # Delay between requests
        if i < count - 1:  # Don't delay after the last request
            time.sleep(delay)
    
    print("-" * 50)
    print(f"Summary: {success_count} successful, {error_count} failed")
    
    if success_count > 0:
        print(f"Success rate: {(success_count / count) * 100:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Send fake log events to the dashboard')
    parser.add_argument('--count', type=int, default=10, help='Number of logs to send (default: 10)')
    parser.add_argument('--server-id', default='test-server-01', help='Server ID to use (default: test-server-01)')
    parser.add_argument('--url', default='http://localhost:5000', help='Dashboard URL (default: http://localhost:5000)')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between requests in seconds (default: 0.1)')
    parser.add_argument('--agent-key', required=True, help='Agent key for HMAC signing')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.count < 1:
        print("Error: count must be at least 1")
        return 1
    
    if args.delay < 0:
        print("Error: delay must be non-negative")
        return 1
    
    try:
        send_logs(args.url, args.agent_key, args.server_id, args.count, args.delay)
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
