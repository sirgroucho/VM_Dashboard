from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import os

Base = declarative_base()

class LogEvent(Base):
    __tablename__ = 'log_events'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    server_id = Column(String(100), nullable=False, index=True)
    host = Column(String(255), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'host': self.host,
            'source': self.source,
            'event_type': self.event_type,
            'severity': self.severity,
            'message': self.message,
            'metadata': self.metadata,
            'ts': self.ts.isoformat() + 'Z' if self.ts else None
        }

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/app.db')

if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
