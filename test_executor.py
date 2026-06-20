from core.database import init_db, SessionLocal
from core import bones, executor

init_db()
db = SessionLocal()

agent_id = bones.create_agent(db, 'Market Analyst', 'analyst', 'guts_market_v1', {'profile': 'analysis'})
bones.update_agent_status(db, agent_id, 'ACTIVE')

result = executor.execute(
    db=db,
    agent_id=agent_id,
    prompt_id='prompt-analyze-market-position-v1',
    prompt_subcategory='analysis',
    workflow_id='workflow-routing-task-dispatch-v1',
    workflow_subcategory='routing',
    user_input='My client John Smith runs a law firm in Dallas. He wants to expand into medical malpractice cases.'
)

print('Prompt:', result.prompt_used)
print('Entities masked:', result.entity_count)
print('Output:', result.final_output[:300])
db.close()
