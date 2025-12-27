from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), default="INFO")  # INFO, SUCCESS, ERROR, WARNING
    module = Column(String(100))  # AUTH, API, JOBS, SYSTEM
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SystemLog(level='{self.level}', module='{self.module}', message='{self.message[:20]}...')>"
