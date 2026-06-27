"""
portal.py
─────────────────────────────────────────────────────────────────────────────
Simple web portal for the hybrid-privacy AI agent engine.
Run with: uvicorn portal:app --reload
Then open: http://localhost:8000
"""

import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

from core.cloud_client import CloudClient
from core.privacy_manager import PrivacyManager
from core.orchestrator import Orchestrator
from core.tenant_router import TenantRouter

app = FastAPI()

# ── Bootstrap the engine ────────────────────────────────────────────────────

router = TenantRouter(
    orchestrator=Orchestrator(
        privacy_manager=PrivacyManager(),
        cloud_client=CloudClient(provider="groq"),
        config_path="industry_profiles/template/prompts.json",
    ),
    tenants_path="industry_profiles/tenants.json",
)

# ── HTML template ────────────────────────────────────────────────────────────

def render_page(result_text: str = "", masked_input: str = "", profile: str = "", elapsed: str = "", error: str = "") -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Engine</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: #0f0f0f;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }}
        h1 {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #ffffff;
        }}
        .subtitle {{
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 40px;
        }}
        .card {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 32px;
            width: 100%;
            max-width: 720px;
            margin-bottom: 24px;
        }}
        label {{
            display: block;
            font-size: 0.85rem;
            color: #aaa;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        select, textarea {{
            width: 100%;
            background: #111;
            border: 1px solid #333;
            border-radius: 8px;
            color: #e0e0e0;
            padding: 12px;
            font-size: 0.95rem;
            margin-bottom: 20px;
            outline: none;
            transition: border 0.2s;
        }}
        select:focus, textarea:focus {{
            border-color: #555;
        }}
        textarea {{
            height: 140px;
            resize: vertical;
            font-family: inherit;
        }}
        button {{
            background: #ffffff;
            color: #000000;
            border: none;
            border-radius: 8px;
            padding: 12px 28px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        button:hover {{ background: #ddd; }}
        .result-card {{
            background: #111;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            margin-top: 8px;
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 0.95rem;
        }}
        .meta {{
            font-size: 0.78rem;
            color: #555;
            margin-top: 12px;
        }}
        .error {{
            background: #1a0000;
            border: 1px solid #440000;
            border-radius: 8px;
            padding: 16px;
            color: #ff6b6b;
            margin-top: 8px;
        }}
        .badge {{
            display: inline-block;
            background: #222;
            border: 1px solid #333;
            border-radius: 20px;
            padding: 3px 10px;
            font-size: 0.75rem;
            color: #888;
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <h1>AI Agent Engine</h1>
    <p class="subtitle">Privacy-preserving AI — PII masked locally before any cloud processing</p>

    <div class="card">
        <form method="post" action="/run">
            <label>Industry Profile</label>
            <select name="tenant_id">
                <option value="demo_tenant">General / Demo</option>
                <option value="clinic_nyc">Medical</option>
                <option value="lawfirm_dallas">Legal</option>
                <option value="hedgefund_001">Finance</option>
                <option value="support_team_a">Customer Support</option>
            </select>

            <label>Your Input</label>
            <textarea name="raw_input" placeholder="Type or paste your text here..."></textarea>

            <button type="submit">Run</button>
        </form>
    </div>

    {"<div class='card'><label>Response</label><div class='result-card'>" + result_text + "</div>" +
     "<div class='meta'><span class='badge'>" + profile + "</span><span class='badge'>" + elapsed + "s</span></div>" +
     "<br><label>What was sent to the cloud (PII masked)</label><div class='result-card'>" + masked_input + "</div></div>"
     if result_text else ""}

    {"<div class='card'><div class='error'>" + error + "</div></div>" if error else ""}

</body>
</html>
"""

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return render_page()


@app.post("/run", response_class=HTMLResponse)
async def run(tenant_id: str = Form(...), raw_input: str = Form(...)):
    if not raw_input.strip():
        return render_page(error="Please enter some text.")
    try:
        result = router.run(tenant_id, raw_input)
        return render_page(
            result_text=result.final_text,
            masked_input=result.orchestrator_result.masked_input,
            profile=result.profile_used,
            elapsed=f"{result.elapsed_seconds:.2f}",
        )
    except Exception as e:
        return render_page(error=str(e))