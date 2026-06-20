"""
core/executor.py
"""
import time
from dataclasses import dataclass
from sqlalchemy.orm import Session
from core.library import load_prompt, load_workflow
from core.bones import log_execution_start, log_execution_complete
from core.cloud_client import CloudClient
from core.privacy_manager import PrivacyManager

pm = PrivacyManager()
cloud = CloudClient(provider="groq")

@dataclass
class ExecutionResult:
    agent_id: str
    prompt_used: str
    workflow_used: str
    masked_input: str
    raw_output: str
    final_output: str
    elapsed_seconds: float
    entity_count: int

def execute(db, agent_id, prompt_id, prompt_subcategory, workflow_id, workflow_subcategory, user_input):
    t_start = time.perf_counter()
    exec_id = log_execution_start(db, agent_id)
    try:
        prompt = load_prompt(prompt_subcategory, prompt_id)
        workflow = load_workflow(workflow_subcategory, workflow_id)
        masked_text, entity_map = pm.mask(user_input)
        system_prompt = f"You are a {prompt['name']} agent. {prompt['purpose']}"
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": masked_text}]
        response = cloud.complete(messages)
        final_output = pm.unmask(response.content, entity_map)
        elapsed = time.perf_counter() - t_start
        log_execution_complete(db, exec_id, success=True, latency_ms=int(elapsed * 1000))
        return ExecutionResult(agent_id=agent_id, prompt_used=prompt['name'], workflow_used=workflow['name'], masked_input=masked_text, raw_output=response.content, final_output=final_output, elapsed_seconds=elapsed, entity_count=len(entity_map))
    except Exception as e:
        elapsed = time.perf_counter() - t_start
        log_execution_complete(db, exec_id, success=False, latency_ms=int(elapsed * 1000), error=str(e))
        raise
