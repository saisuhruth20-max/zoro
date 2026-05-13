"""
Web dashboard — a lightweight Flask app that serves bot statistics.
Runs in a background daemon thread alongside the Discord bot.
"""

import os
import threading

from flask import Flask, jsonify, render_template

from utils.stats import stats

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.urandom(24)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/api/stats")
def api_stats():
    """Return JSON stats snapshot — polled by the dashboard every few seconds."""
    return jsonify(stats.get_snapshot())


@app.route("/health")
def health():
    """Health check endpoint for Railway / uptime monitors."""
    return jsonify({"status": "ok", "uptime": stats.get_uptime()})


# ── Server startup ─────────────────────────────────────────────────────────────

def run_dashboard() -> None:
    """
    Start the Flask development server in a daemon thread.

    Uses the PORT environment variable (Railway injects this automatically).
    Falls back to port 8080 if PORT is not set.
    """
    port = int(os.getenv("PORT", 8080))
    # Disable the reloader — it forks the process which breaks daemon threads
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def start_dashboard_thread() -> threading.Thread:
    """Spawn and return the dashboard background thread."""
    thread = threading.Thread(target=run_dashboard, daemon=True, name="DashboardThread")
    thread.start()
    return thread
