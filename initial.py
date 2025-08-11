import os
import json
from getpass import getpass
from werkzeug.security import generate_password_hash


# Where to store the output file
USER_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "secrets", "users.json"))

import os, json, io

# create empty JSON if missing or 0-byte
if (not os.path.exists(USER_FILE)) or os.stat(USER_FILE).st_size == 0:
    os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# load, but tolerate junk/empty
try:
    with open(USER_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
except json.JSONDecodeError:
    users = {}

def main():
    print("🛠  Create a new user for the dashboard")

    username = input("Username: ").strip()
    password = getpass("Password (hidden): ").strip()
    access = input("Access (minecraft/git): ").strip().lower()
    mcrole = input("Minecraft Role (admin/viewer): ").strip().lower()

    if access not in ("minecraft", "git"):
        print("❌ Invalid access type.")
        return

    # Create file if it doesn't exist
    if not os.path.exists(USER_FILE):
        os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
        with open(USER_FILE, "w") as f:
            json.dump({}, f)

    with open(USER_FILE, "r") as f:
        users = json.load(f)

    if username in users:
        print(f"❌ User '{username}' already exists.")
        return

    users[username] = {
        "password_hash": generate_password_hash(password),
        "access": access,
        "mcrole": mcrole
    }

    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

    print(f"✅ User '{username}' added successfully to {USER_FILE}")

if __name__ == "__main__":
    main()
