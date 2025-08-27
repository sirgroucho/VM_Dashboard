# routes/authz.py
from flask import Blueprint, request, session, Response
from ipaddress import ip_address, ip_network
from models import db, User, Allowlist  # your SQLAlchemy models

bp = Blueprint("authz", __name__)

SERVICE_ROLE = {
    "nextcloud": "nc_user",
    "jellyfin":  "media_user",
    "dashboard": "user",
}

def ip_allowed(service, client_ip):
    rules = Allowlist.query.filter_by(service=service).all()  # cidr strings
    if not rules:
        return True  # if you want allowlist optional
    ip = ip_address(client_ip)
    return any(ip in ip_network(r.cidr) for r in rules)

@bp.get("/auth/nginx")
def auth_nginx():
    svc = request.args.get("service")
    client_ip = request.headers.get("X-Real-IP", request.remote_addr)

    uid = session.get("user_id")
    if not uid:
        return Response(status=401)
    user = User.query.get(uid)
    if not user or not user.is_active:
        return Response(status=403)
    need_role = SERVICE_ROLE.get(svc)
    if need_role and not user.has_role(need_role):
        return Response(status=403)
    if not ip_allowed(svc, client_ip):
        return Response(status=403)
    return Response(status=200)
