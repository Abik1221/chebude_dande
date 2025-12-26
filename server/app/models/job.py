from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Language(Base):
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    tts_voice = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Language(code='{self.code}', name='{self.name}')>"


class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    type = Column(String(50), default="string")  # string, integer, boolean, json
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Setting(key='{self.key}', type='{self.type}')>"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), default="PENDING", nullable=False)
    input_file_path = Column(String(500), nullable=False)
    description_text = Column(Text, nullable=False)
    target_language = Column(String(10), nullable=False)
    output_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, default=0)  # 0-100 percentage
    
    def __repr__(self):
        return f"<Job(id={self.id}, status='{self.status}', target_language='{self.target_language}')>"