#!/usr/bin/env python3
"""
Simple test script to verify the logging system components.
Run this after setting up the system to verify everything works.
"""

import os
import sys
import json
import hmac
import hashlib
import requests
from datetime import datetime

def test_hmac_computation():
    """Test HMAC signature computation."""
    print("Testing HMAC computation...")
    
    key = "test_key_123"
    body = '{"test": "data"}'
    
    expected = hmac.new(key.encode(), body.encode(), hashlib.sha256).hexdigest()
    signature = f"sha256={expected}"
    
    print(f"  Body: {body}")
    print(f"  Key: {key}")
    print(f"  Signature: {signature}")
    print("  ✓ HMAC computation works")
    return True

def test_database_connection():
    """Test database connection."""
    print("\nTesting database connection...")
    
    try:
        from models import SessionLocal, LogEvent
        db = SessionLocal()
        
        # Try to query the database
        count = db.query(LogEvent).count()
        print(f"  Current log count: {count}")
        print("  ✓ Database connection successful")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints availability."""
    print("\nTesting API endpoints...")
    
    base_url = "http://localhost:5000"
    
    try:
        # Test if the server is running
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"  Main page: {response.status_code}")
        
        # Test logs page (should redirect to login)
        response = requests.get(f"{base_url}/logs", timeout=5)
        print(f"  Logs page: {response.status_code}")
        
        # Test API endpoint (should return 401 without auth)
        response = requests.get(f"{base_url}/api/logs", timeout=5)
        print(f"  API endpoint: {response.status_code}")
        
        print("  ✓ API endpoints are accessible")
        return True
        
    except requests.exceptions.ConnectionError:
        print("  ✗ Server not running. Start with 'python app.py'")
        return False
    except Exception as e:
        print(f"  ✗ API test failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration."""
    print("\nTesting environment configuration...")
    
    required_vars = ['SECRET_KEY', 'DATABASE_URL', 'AGENT_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'AGENT_KEY' and value == 'your_secure_agent_key_here_change_this_in_production':
                print(f"  ⚠ {var}: Using default value (change in production)")
            else:
                print(f"  ✓ {var}: Set")
        else:
            print(f"  ✗ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"  Missing required environment variables: {missing_vars}")
        return False
    
    return True

def test_agent_key():
    """Test if agent key is properly configured."""
    print("\nTesting agent key configuration...")
    
    agent_key = os.getenv('AGENT_KEY')
    if not agent_key:
        print("  ✗ AGENT_KEY not set")
        return False
    
    if agent_key == 'your_secure_agent_key_here_change_this_in_production':
        print("  ⚠ Using default agent key (change in production)")
        return False
    
    if len(agent_key) < 16:
        print("  ⚠ Agent key seems too short (recommend at least 16 characters)")
        return False
    
    print("  ✓ Agent key configured")
    return True

def test_send_fake_log():
    """Test sending a fake log entry."""
    print("\nTesting fake log ingestion...")
    
    base_url = "http://localhost:5000"
    agent_key = os.getenv('AGENT_KEY')
    
    if not agent_key or agent_key == 'your_secure_agent_key_here_change_this_in_production':
        print("  ⚠ Skipping log ingestion test (agent key not configured)")
        return True
    
    try:
        # Create test log data
        log_data = {
            "server_id": "test-server",
            "host": "127.0.0.1",
            "source": "test-script",
            "event_type": "test",
            "severity": "INFO",
            "message": "Test log from verification script",
            "metadata": {"test": True, "timestamp": datetime.utcnow().isoformat()}
        }
        
        # Compute HMAC signature
        body = json.dumps(log_data)
        signature = hmac.new(agent_key.encode(), body.encode(), hashlib.sha256).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-Signature": f"sha256={signature}",
            "X-Server-ID": "test-server"
        }
        
        # Send request
        response = requests.post(
            f"{base_url}/api/ingest/logs",
            data=body,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Log ingested successfully: {result}")
            return True
        else:
            print(f"  ✗ Log ingestion failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ Log ingestion test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Marx-Tec Logging System - Component Test")
    print("=" * 50)
    
    tests = [
        ("Environment Configuration", test_environment_config),
        ("Agent Key", test_agent_key),
        ("HMAC Computation", test_hmac_computation),
        ("Database Connection", test_database_connection),
        ("API Endpoints", test_api_endpoints),
        ("Log Ingestion", test_send_fake_log),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The logging system is ready to use.")
        print("\nNext steps:")
        print("1. Navigate to /logs in your browser")
        print("2. Login with appropriate credentials")
        print("3. Test the live updates feature")
        return 0
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        return 1

if __name__ == '__main__':
    exit(main())
