from core.database import init_db, SessionLocal
from core.bones import create_agent, update_agent_status, list_agents

SEED_AGENTS = [
    {
        "name": "Offer Angle Generator",
        "agent_type": "generation",
        "guts_id": "groq-llama-3.3-70b",
        "config": {
            "prompt_id": "prompt-generate-offer-angle-v1",
            "prompt_subcategory": "generation",
            "workflow_id": "workflow-routing-task-dispatch-v1",
            "workflow_subcategory": "routing",
            "provider": "groq"
        }
    },
    {
        "name": "Lead Qualifier",
        "agent_type": "analysis",
        "guts_id": "groq-llama-3.3-70b",
        "config": {
            "prompt_id": "prompt-analyze-lead-quality-v1",
            "prompt_subcategory": "analysis",
            "workflow_id": "workflow-routing-task-dispatch-v1",
            "workflow_subcategory": "routing",
            "provider": "groq"
        }
    },
    {
        "name": "Prospect Signals Extractor",
        "agent_type": "extraction",
        "guts_id": "groq-llama-3.3-70b",
        "config": {
            "prompt_id": "prompt-extract-prospect-signals-v1",
            "prompt_subcategory": "extraction",
            "workflow_id": "workflow-routing-task-dispatch-v1",
            "workflow_subcategory": "routing",
            "provider": "groq"
        }
    },
    {
        "name": "Cold Outreach Copywriter",
        "agent_type": "generation",
        "guts_id": "groq-llama-3.3-70b",
        "config": {
            "prompt_id": "prompt-generate-cold-outreach-v1",
            "prompt_subcategory": "generation",
            "workflow_id": "workflow-routing-task-dispatch-v1",
            "workflow_subcategory": "routing",
            "provider": "groq"
        }
    }
]

init_db()
db = SessionLocal()
existing = {a.name for a in list_agents(db)}
for d in SEED_AGENTS:
    if d["name"] not in existing:
        aid = create_agent(db, d["name"], d["agent_type"], d["guts_id"], d["config"])
        update_agent_status(db, aid, "ACTIVE")
        print(f"Created: {d['name']} [{aid}]")
    else:
        print(f"Skipped: {d['name']}")
db.close()
