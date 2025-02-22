from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class ResearchStatus(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class UserRole(str, PyEnum):
    ADMIN = "admin"
    RESEARCHER = "researcher"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.RESEARCHER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    research_tasks = relationship("ResearchTask", back_populates="owner")
    api_keys = relationship("APIKey", back_populates="user")

class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text)
    status = Column(Enum(ResearchStatus), default=ResearchStatus.PENDING)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    continuous_mode = Column(Boolean, default=False)
    max_iterations = Column(Integer, default=1)
    current_iteration = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="research_tasks")
    analytics = relationship("ResearchAnalytics", back_populates="task", uselist=False)
    sources = relationship("ResearchSource", back_populates="task")

class ResearchAnalytics(Base):
    __tablename__ = "research_analytics"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("research_tasks.id"), unique=True)
    processing_time = Column(Integer)  # in milliseconds
    token_count = Column(Integer)
    source_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Performance metrics
    avg_source_processing_time = Column(Float, nullable=True)
    avg_tokens_per_source = Column(Float, nullable=True)
    cache_hit_rate = Column(Float, nullable=True)
    
    # Relationships
    task = relationship("ResearchTask", back_populates="analytics")

class ResearchSource(Base):
    __tablename__ = "research_sources"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("research_tasks.id"))
    url = Column(String)
    title = Column(String, nullable=True)
    relevance_score = Column(Float)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_time = Column(Integer)  # in milliseconds
    
    # Relationships
    task = relationship("ResearchTask", back_populates="sources")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String)
    user_agent = Column(String)
    details = Column(Text, nullable=True)

# Create indexes
from sqlalchemy import Index

Index('ix_research_tasks_status', ResearchTask.status)
Index('ix_research_tasks_owner_created', ResearchTask.owner_id, ResearchTask.created_at.desc())
Index('ix_api_keys_active', APIKey.is_active)
Index('ix_audit_logs_user_timestamp', AuditLog.user_id, AuditLog.timestamp.desc())