# routes/mc.py
from flask import Blueprint, jsonify, render_template
from decorators import minecraft_login_required
from utils.live_store import get_snapshot, get_players_series

mc_bp = Blueprint("mc", __name__, url_prefix="/mc")

@mc_bp.route("/dashboard")
@minecraft_login_required
def dashboard():
    return render_template("mc_dashboard.html")

@mc_bp.route("/live.json")
@minecraft_login_required
def live_json():
    return jsonify({"snapshot": get_snapshot(), "players_series": get_players_series()})
