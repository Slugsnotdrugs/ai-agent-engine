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

@app.route("/library")
def library():
    db = SessionLocal()
    lib = library_summary()
    assets = {
        "prompts": list_assets("prompts"),
        "templates": list_assets("templates"),
        "workflows": list_assets("workflows"),
        "agents": list_assets("agents"),
        "use-cases": list_assets("use-cases"),
    }
    db.close()
    return render_template("library.html", library=lib, assets=assets)
@app.route('/run', methods=['GET', 'POST'])
def run():
    from core.bones import get_agent
    from core.executor import execute
    
    db = SessionLocal()
    agents = [a for a in list_agents(db) if a.status == 'ACTIVE']
    result = None
    error = None
    
    if request.method == 'POST':
        agent_id = request.form.get('agent_id')
        user_input = request.form.get('user_input', '').strip()
        
        if not agent_id or not user_input:
            error = 'Both agent and input are required.'
        else:
            agent = get_agent(db, agent_id)
            if not agent:
                error = 'Agent not found.'
            else:
                try:
                    cfg = agent.config
                    res = execute(
                        db=db,
                        agent_id=agent.id,
                        prompt_id=cfg['prompt_id'],
                        prompt_subcategory=cfg['prompt_subcategory'],
                        workflow_id=cfg['workflow_id'],
                        workflow_subcategory=cfg['workflow_subcategory'],
                        user_input=user_input
                    )
                    result = {
                        'agent_id': res.agent_id,
                        'prompt_used': res.prompt_used,
                        'workflow_used': res.workflow_used,
                        'masked_input': res.masked_input,
                        'final_output': res.final_output,
                        'elapsed': f'{res.elapsed_seconds:.2f}s',
                        'entities': res.entity_count
                    }
                except Exception as e:
                    error = str(e)
                    
    db.close()
    return render_template('run.html', agents=agents, result=result, error=error)
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)
