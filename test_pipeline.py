"""
test_pipeline.py
Quick sanity-check for the full orchestration pipeline.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from core.cloud_client import CloudClient
from core.privacy_manager import PrivacyManager
from core.orchestrator import Orchestrator

def main():
    print("=== Pipeline Test ===\n")

    # 1. Cloud client health check
    print("1. Testing Groq connection...")
    client = CloudClient(provider="groq")
    ok = client.health_check()
    print(f"   Groq health check: {'PASS' if ok else 'FAIL'}\n")
    if not ok:
        print("Check your GROQ_API_KEY in .env")
        sys.exit(1)

    # 2. Full pipeline run
    print("2. Running full pipeline...")
    orch = Orchestrator(
        privacy_manager=PrivacyManager(),
        cloud_client=client,
        config_path="industry_profiles/template/prompts.json",
        default_profile="general",
    )

    test_input = "My name is John Doe and my email is john@example.com. Summarize my privacy rights."
    result = orch.run(test_input, profile="general")

    print(f"   Masked input:  {result.masked_input}")
    print(f"   Final output:  {result.final_text}")
    print(f"   Time: {result.elapsed_seconds:.2f}s")
    print(f"   Entities masked: {result.metadata['entity_count']}")
    print("\n=== PASS ===")

if __name__ == "__main__":
    main()