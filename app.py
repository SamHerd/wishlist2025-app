import streamlit as st
import json
import base64
import requests
from pathlib import Path

st.write("App started (DEBUG)")  # ---------------- DEBUG 1

JSON_PATH = "wishlist.json"

# ---------------------------
# GitHub Configuration
# ---------------------------
st.write("Loading secrets… (DEBUG)")  # ---------------- DEBUG 2
st.write(st.secrets.get("github", "NO_GITHUB FOUND"))  # DEBUG 3

try:
    GITHUB_USER = st.secrets["github"]["username"]
    GITHUB_REPO = st.secrets["github"]["repo"]
    GITHUB_TOKEN = st.secrets["github"]["token"]
    GITHUB_BRANCH = st.secrets["github"].get("branch", "main")
    st.write("Secrets loaded OK (DEBUG)")  # ---------------- DEBUG 4
except Exception as e:
    st.write("❌ Secrets FAILED to load (DEBUG)")
    st.write(str(e))
    raise

GITHUB_URL = (
    f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{JSON_PATH}"
)
st.write(f"GitHub URL: {GITHUB_URL} (DEBUG)")  # ---------------- DEBUG 5


# ---------------------------
# Load Wishlist (GitHub first)
# ---------------------------
def load_data():
    st.write("Entered load_data() (DEBUG)")  # ---------------- DEBUG 6

    try:
        st.write("Calling GitHub… (DEBUG)")  # ---------------- DEBUG 7
        resp = requests.get(
            GITHUB_URL,
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            params={"ref": GITHUB_BRANCH},
            timeout=10,
        )

        st.write(f"GitHub status: {resp.status_code} (DEBUG)")  # ---------------- DEBUG 8

        if resp.status_code == 200:
            payload = resp.json()
            st.write("GitHub returned 200 OK (DEBUG)")  # ---------------- DEBUG 9

            content = payload.get("content", None)
            st.write(f"Content exists? {content is not None} (DEBUG)")  # DEBUG 10

            decoded = base64.b64decode(content).decode("utf-8")
            data = json.loads(decoded)

            # Cache SHA for updating
            st.session_state["wishlist_sha"] = payload.get("sha")
            st.write(f"SHA cached: {payload.get('sha')} (DEBUG)")  # DEBUG 11
            return data

        elif resp.status_code == 404:
            st.write("GitHub returned 404 — new file will be created (DEBUG)")  # DEBUG 12
            st.session_state["wishlist_sha"] = None
            return {"preferences": {}, "items": [], "archive": {}}

        else:
            st.write("GitHub error, falling back to local JSON (DEBUG)")  # DEBUG 13
            st.write(resp.text)
            return load_local()

    except Exception as e:
        st.write(f"EXCEPTION in load_data(): {str(e)} (DEBUG)")  # ---------------- DEBUG 14
        return load_local()


# ---------------------------
# Local fallback loader
# ---------------------------
def load_local():
    st.write("Entered load_local() (DEBUG)")  # ---------------- DEBUG 15

    p = Path(JSON_PATH)
    if not p.exists():
        st.write("Local file not found — returning empty JSON (DEBUG)")  # DEBUG 16
        return {"preferences": {}, "items": [], "archive": {}}

    st.write("Loading local JSON (DEBUG)")  # ---------------- DEBUG 17
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------
# Save to GitHub (always)
# ---------------------------
def save_data(data):
    st.write("save_data() called (DEBUG)")  # ---------------- DEBUG 18

    json_str = json.dumps(data, indent=2)
    b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    sha = st.session_state.get("wishlist_sha")
    st.write(f"Using SHA: {sha} (DEBUG)")  # ---------------- DEBUG 19

    payload = {
        "message": "Update wishlist.json from Streamlit app",
        "content": b64,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha
        st.write("Included SHA in payload (DEBUG)")  # DEBUG 20

    st.write("Sending PUT request to GitHub… (DEBUG)")  # ---------------- DEBUG 21
    resp = requests.put(
        GITHUB_URL,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        },
        json=payload,
        timeout=10,
    )

    st.write(f"GitHub PUT status: {resp.status_code} (DEBUG)")  # DEBUG 22

    if resp.status_code in (200, 201):
        new_sha = resp.json()["content"]["sha"]
        st.session_state["wishlist_sha"] = new_sha
        st.write(f"Updated SHA -> {new_sha} (DEBUG)")  # DEBUG 23
    else:
        st.error(f"GitHub update FAILED:\n{resp.text}")
