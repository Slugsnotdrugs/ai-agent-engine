"""
example_usage.py
────────────────────────────────────────────────────────────────────────────
End-to-end smoke test / quick-start for the hybrid-privacy agent engine.

Run with:
  GROQ_API_KEY=gsk_... python example_usage.py

Switch provider:
  CLOUD_PROVIDER=together TOGETHER_API_KEY=... python example_usage.py
"""

import logging
import os
import sys

# ── Ensure project root is on sys.path ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from core.cloud_client import CloudClient
from core.orchestrator import Orchestrator
from core.privacy_manager import PrivacyManager

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(name)s  %(message)s",
)


def main() -> None:
    # 1. Instantiate components
    pm     = PrivacyManager()
    client = CloudClient()                  # reads CLOUD_PROVIDER + key from env
    orch   = Orchestrator(
        privacy_manager=pm,
        cloud_client=client,
        config_path="industry_profiles/template/prompts.json",
        default_profile="general",
    )

    print("Available profiles:", orch.available_profiles)
    print()

    # ── Medical example ──────────────────────────────────────────────────────
    medical_note = (
        "Patient John Doe (DOB 03/15/1978, SSN 123-45-6789) presented on "
        "04/10/2024 with complaints of chest pain. Contact: john.doe@email.com, "
        "phone 555-867-5309. Prescribed metoprolol 50 mg twice daily."
    )

    print("=" * 60)
    print("PROFILE: medical")
    print("RAW INPUT:")
    print(medical_note)
    print()

    result = orch.run(medical_note, profile="medical")

    print("MASKED INPUT SENT TO CLOUD:")
    print(result.masked_input)
    print()
    print("FINAL RESPONSE (entities restored):")
    print(result.final_text)
    print()
    print(f"Elapsed: {result.elapsed_seconds:.2f}s | {result.cloud_response.usage_summary}")
    print("=" * 60)

    # ── Finance example ──────────────────────────────────────────────────────
    fin_report = (
        "Quarterly review for client Sarah Connor (ACC-00412). "
        "Total AUM: $4.2M. Unrealised loss in tech sector: -18%. "
        "Three flagged transactions > $10,000 on 02/28/2024."
    )

    print()
    print("PROFILE: finance")
    result2 = orch.run(fin_report, profile="finance")
    print("FINAL RESPONSE:")
    print(result2.final_text)
    print("=" * 60)


if __name__ == "__main__":
    main()
