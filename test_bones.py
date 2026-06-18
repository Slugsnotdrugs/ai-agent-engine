from core.database import init_db, SessionLocal
from core import bones

init_db()
db = SessionLocal()

# Create an agent
agent_id = bones.create_agent(db, "Legal Contract Analyzer", "analyzer", "guts_legal_v1", {"profile": "legal"})
print(f"Created agent: {agent_id}")

# Activate it
bones.update_agent_status(db, agent_id, "ACTIVE")
print("Status updated to ACTIVE")

# Log an execution
exec_id = bones.log_execution_start(db, agent_id)
bones.log_execution_complete(db, exec_id, success=True, latency_ms=1240)
print(f"Execution logged: {exec_id}")

# System metrics
metrics = bones.get_system_metrics(db)
print(f"Metrics: {metrics}")

db.close()
print("Bones test passed.")
