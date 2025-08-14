#!/usr/bin/env python3
"""
Database initialization script.
Creates the database and tables for the logging system.
"""

import os
import sys
import sqlite3
from pathlib import Path

def init_sqlite_db():
    """Initialize SQLite database."""
    # Get database path from environment or use default
    db_path = os.getenv('DATABASE_URL', 'sqlite:///data/app.db')
    
    if db_path.startswith('sqlite:///'):
        db_file = db_path.replace('sqlite:///', '')
    else:
        db_file = 'data/app.db'
    
    # Ensure data directory exists
    data_dir = Path(db_file).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Initializing SQLite database: {db_file}")
    
    # Connect to database (will create if doesn't exist)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create log_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT NOT NULL,
            host TEXT NOT NULL,
            source TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            metadata TEXT,
            ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    print("Creating database indexes...")
    
    # Index on timestamp (most important for pagination)
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_ts 
        ON log_events (ts DESC)
    ''')
    
    # Index on server_id + timestamp
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_server_ts 
        ON log_events (server_id, ts DESC)
    ''')
    
    # Index on event_type + timestamp
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_type_ts 
        ON log_events (event_type, ts DESC)
    ''')
    
    # Index on severity + timestamp
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_severity_ts 
        ON log_events (severity, ts DESC)
    ''')
    
    # Index on server_id
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_server_id 
        ON log_events (server_id)
    ''')
    
    # Index on host
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_host 
        ON log_events (host)
    ''')
    
    # Index on source
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_source 
        ON log_events (source)
    ''')
    
    # Index on event_type
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_event_type 
        ON log_events (event_type)
    ''')
    
    # Index on severity
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_log_events_severity 
        ON log_events (severity)
    ''')
    
    # Commit changes
    conn.commit()
    
    # Verify table creation
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='log_events'")
    if cursor.fetchone():
        print("✓ log_events table created successfully")
    else:
        print("✗ Failed to create log_events table")
        return False
    
    # Check indexes
    cursor.execute("PRAGMA index_list(log_events)")
    indexes = cursor.fetchall()
    print(f"✓ Created {len(indexes)} indexes")
    
    # Show table info
    cursor.execute("PRAGMA table_info(log_events)")
    columns = cursor.fetchall()
    print("\nTable structure:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
    
    conn.close()
    print(f"\n✓ Database initialization completed successfully!")
    return True

def init_postgres_db():
    """Initialize PostgreSQL database."""
    print("PostgreSQL initialization not yet implemented.")
    print("Please use SQLAlchemy migrations or create tables manually.")
    return False

def main():
    """Main function."""
    print("Database Initialization Script")
    print("=" * 40)
    
    # Check environment
    db_url = os.getenv('DATABASE_URL', 'sqlite:///data/app.db')
    
    if db_url.startswith('sqlite://'):
        success = init_sqlite_db()
    elif db_url.startswith('postgresql://'):
        success = init_postgres_db()
    else:
        print(f"Unsupported database URL: {db_url}")
        print("Supported: sqlite:///path/to/db or postgresql://...")
        return 1
    
    if success:
        print("\nNext steps:")
        print("1. Set AGENT_KEY in your environment")
        print("2. Start the Flask application")
        print("3. Test with: python scripts/send_fake_logs.py --agent-key YOUR_KEY")
        return 0
    else:
        print("\nDatabase initialization failed!")
        return 1

if __name__ == '__main__':
    exit(main())
