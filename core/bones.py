"""
core/bones.py
─────────────────────────────────────────────────────────────────────────────
Bones: The rigid orchestration core.
Handles agent lifecycle, state transitions, and execution logging.
Zero business logic — completely config-driven.
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from core.database import Agent, AgentExecutionLog, SystemAlert, get_db, SessionLocal

# ── Valid state transitions ───────────────────────────────────────────────────

VALID_TRANSITIONS = {
    "PROVISIONED": ["ACTIVE", "ARCHIVED"],
    "ACTIVE":      ["PAUSED", "FAILED", "ARCHIVED"],
    "PAUSED":      ["ACTIVE", "ARCHIVED"],
    "FAILED":      ["ACTIVE", "ARCHIVED"],
    "ARCHIVED":    [],
}

# ── Agent management ──────────────────────────────────────────────────────────

def create_agent(db: Session, name: str, agent_type: str, guts_id: str, config: dict, owner_id: int = 1) -> str:
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"
    agent = Agent(
        id=agent_id,
        name=name,
        type=agent_type,
        guts_id=guts_id,
        config=config,
        owner_id=owner_id,
        status="PROVISIONED",
    )
    db.add(agent)
    db.commit()
    return agent_id


def get_agent(db: Session, agent_id: str) -> Agent | None:
    return db.query(Agent).filter(Agent.id == agent_id).first()


def list_agents(db: Session) -> list[Agent]:
    return db.query(Agent).all()


def update_agent_status(db: Session, agent_id: str, new_status: str) -> None:
    agent = get_agent(db, agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found.")

    allowed = VALID_TRANSITIONS.get(agent.status, [])
    if new_status not in allowed:
        raise ValueError(f"Invalid transition: {agent.status} → {new_status}. Allowed: {allowed}")

    agent.status = new_status
    agent.updated_at = datetime.utcnow()
    db.commit()


# ── Execution logging ─────────────────────────────────────────────────────────

def log_execution_start(db: Session, agent_id: str, execution_type: str = "manual") -> str:
    exec_id = f"exec_{uuid.uuid4().hex[:12]}"
    log = AgentExecutionLog(
        id=exec_id,
        agent_id=agent_id,
        execution_type=execution_type,
        status="running",
    )
    db.add(log)
    db.commit()
    return exec_id


def log_execution_complete(db: Session, exec_id: str, success: bool, latency_ms: int, error: str = None) -> None:
    log = db.query(AgentExecutionLog).filter(AgentExecutionLog.id == exec_id).first()
    if not log:
        return
    log.status = "success" if success else "error"
    log.latency_ms = latency_ms
    log.error_message = error
    db.commit()


# ── System alerts ─────────────────────────────────────────────────────────────

def create_alert(db: Session, title: str, message: str, severity: str = "info") -> None:
    alert = SystemAlert(
        id=f"alert_{uuid.uuid4().hex[:12]}",
        title=title,
        message=message,
        severity=severity,
    )
    db.add(alert)
    db.commit()


def get_unresolved_alerts(db: Session) -> list[SystemAlert]:
    return db.query(SystemAlert).filter(SystemAlert.resolved == False).all()


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_system_metrics(db: Session) -> dict:
    active_agents = db.query(Agent).filter(Agent.status == "ACTIVE").count()
    total_agents = db.query(Agent).count()
    unresolved_alerts = db.query(SystemAlert).filter(SystemAlert.resolved == False).count()

    return {
        "active_agents": active_agents,
        "total_agents": total_agents,
        "unresolved_alerts": unresolved_alerts,
    }
