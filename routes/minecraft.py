from flask import Blueprint, session, render_template, request, jsonify
from utils.signal_log import store_event, get_events
from utils.mod_update_trigger import send_update_to_homelab

mc_bp = Blueprint("mc", __name__, url_prefix="/mc")

from decorators import minecraft_login_required  # if in another file

@mc_bp.route("/dashboard")
@minecraft_login_required
def dashboard():
    events = get_events()
    return render_template("mc_dashboard.html", events=events)

@mc_bp.route("/signal", methods=["POST"])
@minecraft_login_required
def signal():
    data = request.json
    store_event(data)
    return jsonify({"status": "ok"}), 200

@mc_bp.route("/update_modpack", methods=["POST"])
@minecraft_login_required
def update_modpack():
    version = request.form.get("version")
    success = send_update_to_homelab(version)
    return jsonify({"status": "sent" if success else "failed"})
