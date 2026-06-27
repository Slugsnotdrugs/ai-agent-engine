import time
from core.database import SessionLocal
from core.bones import log_execution_start, log_execution_complete
from core import executor as ex

class Chainer:
    def __init__(self):
        self.db = SessionLocal()

    def run_chain(self, steps: list, initial_input: str) -> dict:
        current_input = initial_input
        results = []

        for i, step in enumerate(steps):
            print(f"\n[Chainer] Step {i+1}/{len(steps)} - Agent: {step['agent_id']}")
            start = time.time()

            try:
                result = ex.execute(
                    db=self.db,
                    agent_id=step["agent_id"],
                    prompt_id=step["prompt_id"],
                    prompt_subcategory=step["prompt_subcategory"],
                    workflow_id=step["workflow_id"],
                    workflow_subcategory=step["workflow_subcategory"],
                    user_input=current_input
                )
                latency = int((time.time() - start) * 1000)
                print(f"[Chainer] Step {i+1} complete ({latency}ms)")
                current_input = result.final_output
                results.append({"step": i+1, "agent_id": step["agent_id"], "output": result.final_output})

            except Exception as e:
                latency = int((time.time() - start) * 1000)
                print(f"[Chainer] Step {i+1} FAILED: {e}")
                results.append({"step": i+1, "agent_id": step["agent_id"], "error": str(e)})
                break

        return {"steps_completed": len(results), "results": results, "final_output": current_input}

    def close(self):
        self.db.close()
