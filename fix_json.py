import json

files = {
  'library/agents/orchestrators/agent-orchestrator-master-router-v1.json': {
    'id': 'agent-orchestrator-master-router-v1',
    'type': 'agent',
    'category': 'agents',
    'subcategory': 'orchestrators',
    'name': 'Master Router',
    'version': '1.0.0',
    'role': 'Classify incoming work and assign the correct workflow and specialist.',
    'allowed_workflows': ['workflow-routing-task-dispatch-v1'],
    'allowed_prompt_categories': ['analysis', 'extraction', 'evaluation'],
    'handoff_targets': ['specialists', 'reviewers', 'safety'],
    'tags': ['router', 'orchestration', 'control-layer'],
    'status': 'draft'
  },
  'library/prompts/extraction/prompt-extract-client-risks-v1.json': {
    'id': 'prompt-extract-client-risks-v1',
    'type': 'prompt',
    'category': 'prompts',
    'subcategory': 'extraction',
    'name': 'Extract Client Risks',
    'version': '1.0.0',
    'purpose': 'Extract risks from client data.',
    'inputs': ['source_text', 'business_context', 'risk_focus'],
    'output_format': 'json',
    'tags': ['extraction', 'risk', 'client', 'json'],
    'status': 'draft'
  },
  'library/prompts/transformation/prompt-transform-notes-to-summary-v1.json': {
    'id': 'prompt-transform-notes-to-summary-v1',
    'type': 'prompt',
    'category': 'prompts',
    'subcategory': 'transformation',
    'name': 'Transform Notes to Summary',
    'version': '1.0.0',
    'purpose': 'Convert raw notes into a clean structured summary.',
    'inputs': ['raw_notes', 'target_audience', 'tone', 'length_preference'],
    'output_format': 'structured_summary',
    'tags': ['transformation', 'summary', 'notes', 'cleanup'],
    'status': 'draft'
  }
}

for path, data in files.items():
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print('Fixed:', path)
