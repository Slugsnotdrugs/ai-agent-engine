"""
seed_agents.py
─────────────────────────────────────────────────────────────────────────────
Registers a starter set of ACTIVE agents in the database so you can
immediately test the /run endpoint without using the Builder UI.

Run once:
    python seed_agents.py

Safe to re-run: skips agents that already exist by name.
Each agent config points to real files in the library/ folder.
"""
from core.database import init_db, SessionLocal
from core.bones import create_agent, update_agent_status, list_agents

# ── Seed definitions ──────────────────────────────────────────────────────────
# Each dict becomes one row in the agents table.
# prompt_subcategory + prompt_id must match a real file:
#   library/prompts/<prompt_subcategory>/<prompt_id>.json
# workflow_subcategory + workflow_id must match a real file:
#   library/workflows/<workflow_subcategory>/<workflow_id>.json

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
            "provider": "groq",
        },
    },
    {
        "name": "Lead Qualifier",
        "agent_type": "analysis",
        "guts_id": "groq-llama-3.3-70b",
        "config": {
            "prompt_id": "prompt-analyze-lead-qualify-v1",
            "prompt_subcategory": "analysis",
            "workflow_id": "workflow-routing-task-dispatch-v1",
            "workflow_subcategory": "routing",
            "provider": "groq",
        },
    },
    {
        "name": "Contact Data Extractor",
        "agent_type": "extraction",
        "guts_id": "groq-llama-3.3-70b",
        "config": {
            "prompt_id": "prompt-extract-contact-data-v1",
            "prompt_subcategory": "extraction",
            "workflow_id": "workflow-routing-task-dispatch-v1",
            "workflow_subcategory": "routing",
            "provider": "groq",
        },
    },
]


def seed():
    init_db()
    db = SessionLocal()

    # Get existing agent names to avoid duplicates
    existing_names = {a.name for a in list_agents(db)}

    created = []
    skipped = []

    for defn in SEED_AGENTS:
        if defn["name"] in existing_names:
            skipped.append(defn["name"])
            continue

        agent_id = create_agent(
            db=db,
            name=defn["name"],
            agent_type=defn["agent_type"],
            guts_id=defn["guts_id"],
            config=defn["config"],
        )
        update_agent_status(db, agent_id, "ACTIVE")
        created.append((defn["name"], agent_id))

    db.close()

    print("\n── Seed complete ─────────────────────────────────")
    if created:
        print(f"  Created {len(created)} agent(s):")
        for name, aid in created:
            print(f"    ✓  {name}  [{aid}]")
    if skipped:
        print(f"  Skipped {len(skipped)} already-existing agent(s):")
        for name in skipped:
            print(f"    –  {name}")
    print("──────────────────────────────────────────────────\n")
    print("You can now visit http://localhost:8000/run to test them.")


if __name__ == "__main__":
    seed()
