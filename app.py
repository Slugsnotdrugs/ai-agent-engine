from flask import Flask, render_template, request
from core.database import init_db, SessionLocal
from core.bones import get_system_metrics, list_agents, create_agent, update_agent_status
from core.library import library_summary, list_assets

app = Flask(__name__)
init_db()

@app.route("/")
def dashboard():
    db = SessionLocal()
    metrics = get_system_metrics(db)
    agents = list_agents(db)
    lib = library_summary()
    db.close()
    return render_template("dashboard.html", metrics=metrics, agents=agents, library=lib)

@app.route("/builder", methods=["GET", "POST"])
def builder():
    db = SessionLocal()
    prompts = list_assets("prompts")
    workflows = list_assets("workflows")
    success = None
    error = None
    if request.method == "POST":
        try:
            name = request.form["name"]
            agent_type = request.form["type"]
            guts_id = request.form["guts_id"]
            prompt_parts = request.form["prompt_id"].split("|")
            workflow_parts = request.form["workflow_id"].split("|")
            provider = request.form["provider"]
            config = {"prompt_id": prompt_parts[0], "prompt_subcategory": prompt_parts[1], "workflow_id": workflow_parts[0], "workflow_subcategory": workflow_parts[1], "provider": provider}
            agent_id = create_agent(db, name, agent_type, guts_id, config)
            update_agent_status(db, agent_id, "ACTIVE")
            success = agent_id
        except Exception as e:
            error = str(e)
    db.close()
    return render_template("agent_builder.html", prompts=prompts, workflows=workflows, success=success, error=error)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
