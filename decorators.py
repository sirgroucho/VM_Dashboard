from functools import wraps
from flask import session, redirect, url_for, abort

def minecraft_login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in") or session.get("service") != "minecraft":
            return abort(403)
        return f(*args, **kwargs)
    return wrapped
