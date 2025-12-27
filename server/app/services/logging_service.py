from sqlalchemy.orm import Session
from app.models.system import SystemLog
from typing import List, Optional


class LoggingService:
    def log(self, db: Session, message: str, level: str = "INFO", module: str = "SYSTEM"):
        """Record a system log in the database"""
        try:
            new_log = SystemLog(
                message=message,
                level=level,
                module=module
            )
            db.add(new_log)
            db.commit()
            db.refresh(new_log)
            return new_log
        except Exception as e:
            print(f"Error recording log: {e}")
            db.rollback()
            return None

    def get_logs(self, db: Session, limit: int = 50, offset: int = 0) -> List[SystemLog]:
        """Retrieve recent system logs"""
        return db.query(SystemLog).order_by(SystemLog.timestamp.desc()).offset(offset).limit(limit).all()


# Global logging service instance
logging_service = LoggingService()
