import streamlit as st
import json
import base64
import requests
from pathlib import Path

JSON_PATH = "wishlist.json"

# ---------------------------
# GitHub Configuration
# ---------------------------
GITHUB_USER = st.secrets["github"]["username"]
GITHUB_REPO = st.secrets["github"]["repo"]
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_BRANCH = st.secrets["github"].get("branch", "main")

GITHUB_URL = (
    f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{JSON_PATH}"
)


# ---------------------------
# Load Wishlist (GitHub first)
# ---------------------------
def load_data():
    try:
        resp = requests.get(
            GITHUB_URL,
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            params={"ref": GITHUB_BRANCH},
            timeout=10,
        )

        if resp.status_code == 200:
            payload = resp.json()
            content = payload["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            data = json.loads(decoded)

            # Cache SHA for updating
            st.session_state["wishlist_sha"] = payload["sha"]
            return data

        # File doesn't exist yet → initialize empty
        elif resp.status_code == 404:
            st.session_state["wishlist_sha"] = None
            return {"preferences": {}, "items": [], "archive": {}}

        else:
            st.warning("GitHub load failed — loading local JSON instead.")
            return load_local()

    except Exception:
        return load_local()


# ---------------------------
# Local fallback loader
# ---------------------------
def load_local():
    p = Path(JSON_PATH)
    if not p.exists():
        return {"preferences": {}, "items": [], "archive": {}}

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------
# Save to GitHub (always)
# ---------------------------
def save_data(data):
    json_str = json.dumps(data, indent=2)
    b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    sha = st.session_state.get("wishlist_sha")

    payload = {
        "message": "Update wishlist.json from Streamlit app",
        "content": b64,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha

    resp = requests.put(
        GITHUB_URL,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        },
        json=payload,
        timeout=10,
    )

    if resp.status_code in (200, 201):
        new_sha = resp.json()["content"]["sha"]
        st.session_state["wishlist_sha"] = new_sha
    else:
        st.error(f"GitHub update FAILED:\n{resp.text}")
