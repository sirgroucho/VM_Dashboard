import os
import threading
import time
from datetime import datetime, timedelta
from sqlalchemy import delete
from models import LogEvent, SessionLocal

class LogRetentionService:
    """Service for managing log retention and cleanup."""
    
    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        self.running = False
        self.thread = None
        self.cleanup_interval = 24 * 60 * 60  # 24 hours in seconds
    
    def start(self):
        """Start the retention service in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"Log retention service started (retention: {self.retention_days} days)")
    
    def stop(self):
        """Stop the retention service."""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Log retention service stopped")
    
    def _run(self):
        """Main retention service loop."""
        while self.running:
            try:
                self._cleanup_old_logs()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                print(f"Error in retention service: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _cleanup_old_logs(self):
        """Remove logs older than retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        db = SessionLocal()
        try:
            # Count logs to be deleted
            count_query = db.query(LogEvent).filter(LogEvent.ts < cutoff_date)
            to_delete_count = count_query.count()
            
            if to_delete_count > 0:
                # Delete old logs
                delete_query = delete(LogEvent).where(LogEvent.ts < cutoff_date)
                result = db.execute(delete_query)
                db.commit()
                
                print(f"Retention cleanup: deleted {to_delete_count} logs older than {cutoff_date}")
            else:
                print(f"Retention cleanup: no logs older than {cutoff_date}")
                
        except Exception as e:
            db.rollback()
            print(f"Error during retention cleanup: {e}")
        finally:
            db.close()
    
    def manual_cleanup(self) -> int:
        """Manually trigger cleanup and return number of deleted logs."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        db = SessionLocal()
        try:
            # Count and delete old logs
            count_query = db.query(LogEvent).filter(LogEvent.ts < cutoff_date)
            to_delete_count = count_query.count()
            
            if to_delete_count > 0:
                delete_query = delete(LogEvent).where(LogEvent.ts < cutoff_date)
                result = db.execute(delete_query)
                db.commit()
                print(f"Manual cleanup: deleted {to_delete_count} logs older than {cutoff_date}")
            else:
                print(f"Manual cleanup: no logs older than {cutoff_date}")
            
            return to_delete_count
            
        except Exception as e:
            db.rollback()
            print(f"Error during manual cleanup: {e}")
            raise
        finally:
            db.close()
    
    def get_retention_stats(self) -> dict:
        """Get retention statistics."""
        db = SessionLocal()
        try:
            total_logs = db.query(LogEvent).count()
            
            # Count logs by age
            now = datetime.utcnow()
            age_ranges = [
                ("1_day", 1),
                ("7_days", 7),
                ("30_days", 30),
                ("90_days", 90)
            ]
            
            age_counts = {}
            for label, days in age_ranges:
                cutoff = now - timedelta(days=days)
                count = db.query(LogEvent).filter(LogEvent.ts >= cutoff).count()
                age_counts[label] = count
            
            # Count logs that would be deleted in next cleanup
            cutoff_date = now - timedelta(days=self.retention_days)
            to_be_deleted = db.query(LogEvent).filter(LogEvent.ts < cutoff_date).count()
            
            return {
                "total_logs": total_logs,
                "age_distribution": age_counts,
                "to_be_deleted": to_be_deleted,
                "retention_days": self.retention_days,
                "next_cleanup": cutoff_date.isoformat()
            }
            
        finally:
            db.close()

# Global retention service instance
retention_service = LogRetentionService(
    retention_days=int(os.getenv('LOG_RETENTION_DAYS', '30'))
)
