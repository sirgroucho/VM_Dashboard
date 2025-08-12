# routes/ingest.py
import os, time, hmac, hashlib
from flask import Blueprint, request, jsonify
from utils.live_store import update_live
from utils.daily_log import append_log, cleanup_logs

ingest_bp = Blueprint("ingest", __name__)
AGENT_KEY = os.getenv("AGENT_KEY", "").encode()

def verify_hmac(req) -> bool:
    if not AGENT_KEY:
        return False
    body = req.get_data()  # raw bytes
    ts   = req.headers.get("X-Timestamp", "")
    sig  = req.headers.get("X-Signature", "")
    # basic sanity
    if not ts.isdigit() or not sig.startswith("sha256="):
        return False
    # replay window (5 min)
    if abs(time.time() - int(ts)) > 300:
        return False
    expect = "sha256=" + hmac.new(AGENT_KEY, body + ts.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expect)

@ingest_bp.route("/api/ingest", methods=["POST"])
def ingest():
    # size cap
    if request.content_length and request.content_length > 64 * 1024:
        return jsonify({"error":"payload_too_large"}), 413

    if not verify_hmac(request):
        return jsonify({"error":"unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    # optional normalization
    if "player_count" in data and "players_online" not in data:
        data["players_online"] = data["player_count"]
    if "timestamp" in data and "ts" not in data:
        data["ts"] = data["timestamp"]

    update_live(data)     # RAM live cache
    append_log(data)      # daily .ndjson.gz
    if int(time.time()) % 3600 < 3:
        cleanup_logs(31)

    return jsonify({"ok": True})

