from core.library import library_summary, load_prompt, load_agent, list_assets

print("=== Library Summary ===")
summary = library_summary()
for cat, count in summary.items():
    print(f"  {cat}: {count} assets")

print("\n=== Load a prompt ===")
prompt = load_prompt("analysis", "prompt-analyze-market-position-v1")
print(f"  Loaded: {prompt['name']}")

print("\n=== Load an agent ===")
agent = load_agent("orchestrators", "agent-orchestrator-master-router-v1")
print(f"  Loaded: {agent['name']}")

print("\nLibrary test passed.")
