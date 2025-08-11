# routes/ingest.py
import os, time
from flask import Blueprint, request, jsonify
from utils.live_store import update_live
from utils.daily_log import append_log, cleanup_logs

ingest_bp = Blueprint("ingest", __name__)
AGENT_KEY = os.getenv("AGENT_KEY","")

@ingest_bp.route("/api/ingest", methods=["POST"])
def ingest():
    auth = request.headers.get("Authorization","")
    if not auth.startswith("Bearer ") or auth.split(" ",1)[1] != AGENT_KEY:
        return jsonify({"error":"unauthorized"}), 401
    if request.content_length and request.content_length > 64*1024:
        return jsonify({"error":"payload_too_large"}), 413

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error":"invalid_json"}), 400

    update_live(data)     # live (RAM)
    append_log(data)      # durable (disk)
    if int(time.time()) % 3600 < 3:   # lazy hourly cleanup
        cleanup_logs(31)

    return jsonify({"ok": True})
