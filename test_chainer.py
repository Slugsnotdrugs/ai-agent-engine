from core.database import init_db
from core.chainer import Chainer

init_db()

steps = [
    {
        "agent_id": "prospector",
        "prompt_id": "prompt-extract-prospect-signals-v1",
        "prompt_subcategory": "extraction",
        "workflow_id": "workflow-routing-task-dispatch-v1",
        "workflow_subcategory": "routing"
    },
    {
        "agent_id": "copywriter",
        "prompt_id": "prompt-generate-cold-outreach-v1",
        "prompt_subcategory": "generation",
        "workflow_id": "workflow-routing-task-dispatch-v1",
        "workflow_subcategory": "routing"
    }
]

chainer = Chainer()
result = chainer.run_chain(steps, initial_input="Target audience: indie founders building SaaS tools. Platform: Reddit.")
chainer.close()

print("\n=== CHAIN RESULT ===")
for r in result["results"]:
    print(f"\nStep {r['step']} - {r['agent_id']}:")
    print(r.get("output", r.get("error")))
