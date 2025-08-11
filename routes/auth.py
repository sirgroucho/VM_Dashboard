from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os, time
import re

def is_valid_username(username):
    return bool(re.fullmatch(r"[a-zA-Z0-9_-]{3,20}", username))


user_cooldowns = {}  # {username: timestamp}
COOLDOWN_SECONDS = 10


auth_bp = Blueprint('auth', __name__)

secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "userdata", "users.json"))


# --- Helper functions ---

def load_users():
    with open(secrets_path) as f:
        return json.load(f)

def save_users(users):
    os.makedirs(os.path.dirname(USERS_JSON), exist_ok=True)
    tmp = USERS_JSON + ".tmp"
    with open(tmp, "w") as f:
        json.dump(users, f, indent=2)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, USERS_JSON)


# --- Login Route ---

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users()



        now = time.time()
        if not is_valid_username(username):
            flash("Invalid username or password.")
            return redirect(url_for("auth.login"))
        if username in user_cooldowns and now < user_cooldowns[username]:
            wait = int(user_cooldowns[username] - now)
            flash(f"Please wait {wait} seconds before retrying.")
            return redirect(url_for("auth.login"))

        # Trigger cooldown and fail even if the user doesn't exist
        user = users.get(username)
        if not user or not check_password_hash(user.get("password_hash"), password):
            user_cooldowns[username] = now + COOLDOWN_SECONDS
            flash("Invalid username or password.")
            return redirect(url_for("auth.login"))

        # Successful login
        user_cooldowns.pop(username, None)
        session["logged_in"] = True
        session["username"] = username
        session["service"] = user.get("access")
        session["mcrole"] = user.get("mcrole", "viewer")

        if user["access"] == "minecraft":
            return redirect(url_for("mc.dashboard"))
        elif user["access"] == "git":
            return redirect("http://gitea.lab.ts.net:3000")

        flash("Unknown service.")
        return redirect(url_for("auth.login"))

    return render_template("login.html")

#Logout

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))



# --- Create User Route ---

@auth_bp.route("/create", methods=["GET", "POST"])
def create_user():
    if not session.get("logged_in") or session.get("mcrole") != "admin":
        flash("Admin access required.")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        access = request.form.get("access")
        mcrole = request.form.get("mcrole")
        if not password or len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("auth.create_user"))


        users = load_users()

        if username in users:
            return "User already exists", 400

        users[username] = {
            "password_hash": generate_password_hash(password),
            "access": access,
            "mcrole": mcrole
        }

        save_users(users)
        return redirect(url_for("auth.manage_users"))

    return render_template("create_user.html")

# --- User Management Route ---

@auth_bp.route("/users")
def manage_users():
    if not session.get("logged_in") or session.get("mcrole") != "admin":
            flash("Admin access required.")
            return redirect(url_for("auth.login"))

    users = load_users()
    return render_template("users.html", users=users)
