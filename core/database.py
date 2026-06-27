"""
core/database.py
SQLite database setup using SQLAlchemy.
Single source of truth for all data in the system.
"""

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, 
    Boolean, DateTime, Text, JSON, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

DATABASE_URL = "sqlite:///./agent_engine.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Enums ────────────────────────────────────────────────────────────────────

class AgentStatus(str, enum.Enum):
    PROVISIONED = "PROVISIONED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"

class LeadStatus(str, enum.Enum):
    RAW = "raw"
    SCORED = "scored"
    OUTREACHED = "outreached"
    RESPONDED = "responded"
    CONVERTED = "converted"
    REJECTED = "rejected"

class ClientTier(str, enum.Enum):
    STARTER = "Starter"
    PROFESSIONAL = "Professional"
    ENTERPRISE = "Enterprise"


# ── Models ───────────────────────────────────────────────────────────────────

class Agent(Base):
    __tablename__ = "agents"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(64), nullable=False)
    status = Column(String(32), default="PROVISIONED")
    owner_id = Column(Integer, nullable=False)
    guts_id = Column(String(64), nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Client(Base):
    __tablename__ = "clients"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(320), nullable=False, unique=True)
    subscription_tier = Column(String(32), default="Starter")
    monthly_rate = Column(Float, nullable=False)
    status = Column(String(32), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class Lead(Base):
    __tablename__ = "leads"
    id = Column(String(64), primary_key=True)
    company_name = Column(String(255), nullable=False)
    contact_email = Column(String(320), nullable=False)
    contact_name = Column(String(255))
    industry = Column(String(128))
    company_size = Column(String(64))
    score = Column(Integer, default=0)
    status = Column(String(32), default="raw")
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"
    id = Column(String(64), primary_key=True)
    agent_id = Column(String(64), nullable=False)
    execution_type = Column(String(64), nullable=False)
    status = Column(String(32), default="pending")
    error_message = Column(Text)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemAlert(Base):
    __tablename__ = "system_alerts"
    id = Column(String(64), primary_key=True)
    severity = Column(String(32), default="info")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Init ─────────────────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
