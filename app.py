"""
app.py
Meta-Agent Factory — Owner Dashboard (Flask)
"""
from flask import Flask, render_template
from core.database import init_db, SessionLocal
from core.bones import get_system_metrics, list_agents
from core.library import library_summary

app = Flask(__name__)
init_db()

@app.route("/")
def dashboard():
    db = SessionLocal()
    metrics = get_system_metrics(db)
    agents = list_agents(db)
    lib = library_summary()
    db.close()
    return render_template("dashboard.html",
        metrics=metrics,
        agents=agents,
        library=lib
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
