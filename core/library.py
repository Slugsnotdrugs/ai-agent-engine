"""
core/library.py
─────────────────────────────────────────────────────────────────────────────
Library Loader: Reads and resolves assets from the library system.
Loads prompts, templates, workflows, agents, and use-cases from JSON files.
Nothing is hardcoded — everything comes from the library folder.
"""

import json
from pathlib import Path
from typing import Any

LIBRARY_ROOT = Path(__file__).parent.parent / "library"


# ── Generic loader ────────────────────────────────────────────────────────────

def load_asset(category: str, subcategory: str, asset_id: str) -> dict[str, Any]:
    path = LIBRARY_ROOT / category / subcategory / f"{asset_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Asset not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def list_assets(category: str, subcategory: str = None) -> list[dict]:
    base = LIBRARY_ROOT / category
    if subcategory:
        base = base / subcategory
    if not base.exists():
        return []
    assets = []
    for path in base.rglob("*.json"):
        if path.name == "index.json":
            continue
        with path.open(encoding="utf-8") as f:
            assets.append(json.load(f))
    return assets


# ── Typed loaders ─────────────────────────────────────────────────────────────

def load_prompt(subcategory: str, prompt_id: str) -> dict:
    return load_asset("prompts", subcategory, prompt_id)

def load_template(subcategory: str, template_id: str) -> dict:
    return load_asset("templates", subcategory, template_id)

def load_workflow(subcategory: str, workflow_id: str) -> dict:
    return load_asset("workflows", subcategory, workflow_id)

def load_agent(subcategory: str, agent_id: str) -> dict:
    return load_asset("agents", subcategory, agent_id)

def load_use_case(subcategory: str, use_case_id: str) -> dict:
    return load_asset("use-cases", subcategory, use_case_id)


# ── Use case resolver ─────────────────────────────────────────────────────────

def resolve_use_case(subcategory: str, use_case_id: str) -> dict:
    """
    Load a use case and resolve all its component references.
    Returns the full assembled use case with all assets loaded.
    """
    use_case = load_use_case(subcategory, use_case_id)
    resolved = {**use_case, "resolved_components": {}}

    for prompt_id in use_case.get("components", {}).get("prompts", []):
        for sub in ["generation", "analysis", "transformation", "extraction", "evaluation"]:
            try:
                resolved["resolved_components"].setdefault("prompts", []).append(
                    load_prompt(sub, prompt_id)
                )
                break
            except FileNotFoundError:
                continue

    for workflow_id in use_case.get("components", {}).get("workflows", []):
        for sub in ["linear", "routing", "review", "parallel", "handoff"]:
            try:
                resolved["resolved_components"].setdefault("workflows", []).append(
                    load_workflow(sub, workflow_id)
                )
                break
            except FileNotFoundError:
                continue

    for agent_id in use_case.get("components", {}).get("agents", []):
        for sub in ["orchestrators", "specialists", "reviewers", "safety", "utilities"]:
            try:
                resolved["resolved_components"].setdefault("agents", []).append(
                    load_agent(sub, agent_id)
                )
                break
            except FileNotFoundError:
                continue

    return resolved


# ── Summary ───────────────────────────────────────────────────────────────────

def library_summary() -> dict:
    categories = ["prompts", "templates", "workflows", "agents", "use-cases"]
    summary = {}
    for cat in categories:
        assets = list_assets(cat)
        summary[cat] = len(assets)
    return summary
