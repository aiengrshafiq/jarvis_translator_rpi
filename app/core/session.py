import json
import os

SESSION_FILE = "assistant_session.json"

def set_verified_user(name: str):
    with open(SESSION_FILE, "w") as f:
        json.dump({"verified_user": name}, f)

def get_verified_user():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
        return data.get("verified_user")
    except Exception:
        return None

def clear_verified_user():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
