import json
import os

LOG_FILE = "signals.json"

def store_event(event):
    log = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            log = json.load(f)
    log.append(event)
    with open(LOG_FILE, "w") as f:
        json.dump(log[-50:], f)  # Keep last 50 events

def get_events():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []
