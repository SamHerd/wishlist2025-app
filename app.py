import streamlit as st
import json
import base64
from pathlib import Path
import requests

JSON_PATH = "wishlist.json"

RAW_BANNER_URL = (
    "https://raw.githubusercontent.com/SamHerd/wishlist2025-app/main/christmas_banner.jpg"
)

# ---------------------------------------------------
# GitHub config helper
# ---------------------------------------------------
def get_github_config():
    try:
        gh = st.secrets["github"]
        return {
            "token": gh["token"],
            "user": gh["username"],
            "repo": gh["repo"],
            "branch": gh.get("branch", "main"),
        }
    except Exception:
        return None


# ---------------------------------------------------
# Load + Save JSON (GitHub + local fallback)
# ---------------------------------------------------
def load_data():
    gh_cfg = get_github_config()

    # Try GitHub first
    if gh_cfg is not None:
        try:
            url = f"https://api.github.com/repos/{gh_cfg['user']}/{gh_cfg['repo']}/contents/{JSON_PATH}"
            headers = {
                "Authorization": f"token {gh_cfg['token']}",
                "Accept": "application/vnd.github+json",
            }
            params = {"ref": gh_cfg["branch"]}
            resp = requests.get(url, headers=headers, params=params, timeout=10)

            if resp.status_code == 200:
                payload = resp.json()
                content_b64 = payload.get("content", "")
                decoded = base64.b64decode(content_b64.encode("utf-8")).decode("utf-8")
                data = json.loads(decoded)

                # Cache SHA for future updates
                st.session_state["wishlist_sha"] = payload.get("sha")
            elif resp.status_code == 404:
                # File not found in repo yet
                data = {"preferences": {}, "items": [], "archive": {}}
                st.session_state["wishlist_sha"] = None
            else:
                # Fallback to local if GitHub fails oddly
                data = _load_local()
                st.warning("Could not load wishlist from GitHub. Using local copy instead.")
        except Exception:
            data = _load_local()
            st.warning("GitHub load failed. Using local wishlist.json if present.")
    else:
        # No GitHub config -> local mode only
        data = _load_local()

    # Ensure keys exist
    if "preferences" not in data:
        data["preferences"] = {}
    if "items" not in data:
        data["items"] = []
    if "archive" not in data:
        data["archive"] = {}

    return data


def _load_local():
    p = Path(JSON_PATH)
    if not p.exists():
        return {"preferences": {}, "items": [], "archive": {}}
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    # Always save locally
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Try syncing to GitHub
    gh_cfg = get_github_config()
    if gh_cfg is None:
        return

    try:
        url = f"https://api.github.com/repos/{gh_cfg['user']}/{gh_cfg['repo']}/contents/{JSON_PATH}"
        headers = {
            "Authorization": f"token {gh_cfg['token']}",
            "Accept": "application/vnd.github+json",
        }

        json_str = json.dumps(data, indent=2)
        content_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": "Update wishlist via Streamlit app",
            "content": content_b64,
            "branch": gh_cfg["branch"],
        }

        sha = st.session_state.get("wishlist_sha")
        if sha:
            payload["sha"] = sha

        resp = requests.put(url, headers=headers, json=payload, timeout=10)

        if resp.status_code in (200, 201):
            resp_data = resp.json()
            content_info = resp_data.get("content", {})
            st.session_state["wishlist_sha"] = content_info.get("sha", sha)
        else:
            st.warning(
                f"Could not sync wishlist to GitHub (status {resp.status_code}). "
                "Changes are still saved locally on the server."
            )
    except Exception:
        # Fail silently for GitHub; local still has the changes
        pass


# ---------------------------------------------------
# Base64 image helpers
# ---------------------------------------------------
def file_to_base64(file):
    if not file:
        return ""
    return base64.b64encode(file.read()).decode("utf-8")


def show_base64_image(b64_str):
    if not b64_str:
        st.write("(no image)")
        return
    st.image(base64.b64decode(b64_str), use_column_width=False)


# ---------------------------------------------------
# Price parser
# ---------------------------------------------------
def parse_price_to_float(text):
    if not text or not text.strip():
        return None, None

    raw = text.strip()
    cleaned = raw.replace("$", "").replace(",", "").strip()

    try:
        return float(cleaned), None
    except ValueError:
        return None, f"Could not understand price: '{raw}'. Use 129.99 or $129.99."


# ---------------------------------------------------
# Streamlit Setup
# ---------------------------------------------------
st.set_page_config(page_title="Sam's Wishlist", layout="wide")
data = load_data()

# ---------------------------------------------------
# GLOBAL BACKGROUND + SNOWFLAKES + TITLE STYLES
# ---------------------------------------------------
st.markdown(
    """
<style>

/* REMOVE TOP PADDING */
[data-testid="stAppViewContainer"] {
    padding-top: 0 !important;
}

/* SOLID ICE BLUE BACKGROUND */
html, body, .stApp {
    background: #e6f5ff !important;
    background-attachment: fixed !important;
    overflow-x: hidden !important;
}

/* SNOWFLAKE BASE STYLE */
.snowflake {
    position: fixed;
    top: -10px;
    font-size: 18px;
    color: rgba(255,255,255,0.9);
    user-select: none;
    pointer-events: none;
    z-index: 1; /* BELOW content, ABOVE background */
    animation: fall linear infinite;
}

/* Snowfall animation */
@keyframes fall {
    0%   { transform: translateY(0) translateX(0); opacity: 1; }
    100% { transform: translateY(110vh) translateX(-40px); opacity: 0; }
}

/* Generate 40 flakes at distinct positions */
"""
    + "\n".join(
        [
            f".flake{n} {{ left: {n * 2.5}%; animation-duration: {4 + (n % 5)}s; }}"
            for n in range(40)
        ]
    )
    + """
/* ---- Banner Style ---- */
img.banner-img {
    width: 100% !important;
    max-height: 600px !important;
    object-fit: cover !important;
    object-position: 50% 30% !important;
    border-radius: 10px !important;
    margin-top: 0px !important;
    box-shadow: 0 0 18px rgba(0,255,180,0.35);
}

/* NEON TITLE STYLING */
h1, h2, h3 {
    font-weight: 900 !important;
    color: #0a3d4f !important;
    text-shadow:
        0 0 8px rgba(0,255,200,0.35),
        0 0 14px rgba(0,255,200,0.25);
}

/* TABS — black text */
.stTabs [data-baseweb="tab"] {
    color: black !important;
    font-weight: 600 !important;
    text-shadow: none !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: black !important;
    text-shadow: none !important;
}

/* ITEM CARD BACKGLOW */
div[data-testid="column"] > div {
    background: rgba(0,255,180,0.03);
    border-radius: 10px;
    padding: 10px 14px;
    box-shadow: 0 0 12px rgba(0,255,180,0.15);
}

/* BUTTONS */
button[kind="primary"] {
    background-color: #0e0e0e !important;
    border: 1px solid #0ff !important;
    box-shadow: 0 0 8px rgba(0,255,180,0.4) !important;
}

</style>
""",
    unsafe_allow_html=True,
)

# Inject snowflakes into the DOM
for n in range(40):
    st.markdown(f'<div class="snowflake flake{n}">❄</div>', unsafe_allow_html=True)

# ---------------------------------------------------
# Title + Banner
# ---------------------------------------------------
st.title("🎁 Sam’s 2025 Christmas Wishlist")

st.markdown(
    f'<img src="{RAW_BANNER_URL}" class="banner-img">',
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# Predefined categories
# ---------------------------------------------------
CATEGORIES = [
    "Shoes",
    "Jacket",
    "Shirts",
    "Outerwear",
    "Menswear",
    "Graphic Tee",
    "Toys",
    "UNT Merch",
    "Amazon",
    "Misc",
]

# ---------------------------------------------------
# Tabs (View, Add, Edit)
# ---------------------------------------------------
tabs = st.tabs(["📜 View Wishlist", "➕ Add a New Item", "✏️ Edit Items"])
tab_view = tabs[0]
tab_add = tabs[1]
tab_edit = tabs[2]

# ---------------------------------------------------
# TAB 1: VIEW WISHLIST
# ---------------------------------------------------
with tab_view:
    st.header("View Sam’s Wishlist")
    st.write("<hr>", unsafe_allow_html=True)

    filter_cat = st.multiselect("Filter by category:", CATEGORIES)
    filter_priority = st.multiselect("Filter by priority:", ["High", "Medium", "Low"])

    col_min, col_max = st.columns(2)
    with col_min:
        min_price_str = st.text_input(
            "Min price (optional):", key="min_price_filter"
        )
    with col_max:
        max_price_str = st.text_input(
            "Max price (optional):", key="max_price_filter"
        )

    search = st.text_input("Search items by name:", key="search_filter")

    filtered = list(data["items"])

    # Category filter
    if filter_cat:
        filtered = [i for i in filtered if i.get("category") in filter_cat]

    # Priority filter
    if filter_priority:
        filtered = [i for i in filtered if i.get("priority") in filter_priority]

    # Price filters
    min_price_val, _ = (
        parse_price_to_float(min_price_str)
        if min_price_str.strip()
        else (None, None)
    )
    max_price_val, _ = (
        parse_price_to_float(max_price_str)
        if max_price_str.strip()
        else (None, None)
    )

    if min_price_val is not None:
        filtered = [
            i
            for i in filtered
            if i.get("price") is not None and i["price"] >= min_price_val
        ]
    if max_price_val is not None:
        filtered = [
            i
            for i in filtered
            if i.get("price") is not None and i["price"] <= max_price_val
        ]

    # Search
    if search.strip():
        s = search.lower()
        filtered = [
            i for i in filtered if s in i.get("name", "").lower()
        ]

    cols = st.columns(2)

    for idx, item in enumerate(filtered):
        with cols[idx % 2]:
            st.write("---")

            show_base64_image(item.get("image", ""))

            st.subheader(item.get("name", "(no name)"))
            st.write(f"**Category:** {item.get('category', 'N/A')}")
            st.write(f"**Priority:** {item.get('priority', 'N/A')}")

            if item.get("size"):
                st.write(f"**Size:** {item['size']}")
            if item.get("style"):
                st.write(f"**Style/Color:** {item['style']}")

            if item.get("price") is not None:
                try:
                    st.write(f"**Price:** ${float(item['price']):,.2f}")
                except Exception:
                    st.write(f"**Price:** {item['price']}")

            if item.get("url"):
                st.write(f"[View Item]({item['url']})")

            purchased_flag = st.checkbox(
                "Purchased?",
                value=item.get("purchased", False),
                key=f"purchased_{idx}",
            )
            if purchased_flag != item.get("purchased", False):
                item["purchased"] = purchased_flag
                save_data(data)

            if st.button("❌ Remove", key=f"rm_{idx}"):
                data["items"].remove(item)
                save_data(data)
                st.warning("Removed.")
                st.rerun()

# ---------------------------------------------------
# TAB 2: ADD NEW ITEM
# ---------------------------------------------------
with tab_add:
    st.header("Add a New Item")
    st.write("<hr>", unsafe_allow_html=True)

    new_url = st.text_input("Item URL:")
    archive_entry = data["archive"].get(new_url, {}) if new_url else {}

    auto_name = archive_entry.get("name", "")
    auto_cat = archive_entry.get("category", "Misc")
    auto_img = archive_entry.get("image", "")
    auto_size = archive_entry.get("size", "")
    auto_style = archive_entry.get("style", "")
    auto_price_val = archive_entry.get("price", None)

    auto_price_str = (
        f"{float(auto_price_val):.2f}"
        if auto_price_val is not None
        else ""
    )

    uploaded_file = st.file_uploader(
        "Upload item image (PNG/JPG)", type=["png", "jpg", "jpeg"]
    )

    name = st.text_input("Item name:", auto_name)
    category = st.selectbox(
        "Category:",
        CATEGORIES,
        index=CATEGORIES.index(auto_cat) if auto_cat in CATEGORIES else 0,
    )
    priority = st.selectbox("Priority:", ["High", "Medium", "Low"])

    size = st.text_input("Size (e.g. 10.5, M, 34x30):", auto_size)
    style = st.text_input("Style / Color (e.g. taupe, dark green):", auto_style)
    price_str = st.text_input(
        "Price (e.g. 129.99 or $129.99):", auto_price_str
    )

    if st.button("Add Item"):
        if not new_url.strip():
            st.error("Please enter an item URL.")
            st.stop()
        if not name.strip():
            st.error("Please enter an item name.")
            st.stop()

        price_val, price_err = parse_price_to_float(price_str)
        if price_err:
            st.error(price_err)
            st.stop()

        img_b64 = file_to_base64(uploaded_file) if uploaded_file else auto_img

        item = {
            "name": name,
            "url": new_url,
            "image": img_b64,
            "category": category,
            "priority": priority,
            "purchased": False,
            "size": size,
            "style": style,
            "price": price_val,
        }

        data["items"].append(item)
        data["archive"][new_url] = item.copy()

        save_data(data)
        st.success("Item added!")
        st.rerun()

# ---------------------------------------------------
# TAB 3: EDIT EXISTING ITEMS
# ---------------------------------------------------
with tab_edit:
    st.header("Edit Existing Items")
    st.write("<hr>", unsafe_allow_html=True)

    if not data["items"]:
        st.info("No items to edit yet.")
    else:
        # Build labels like "1. Jacket Name"
        labels = [
            f"{i+1}. {item.get('name', '(no name)')}" for i, item in enumerate(data["items"])
        ]
        selected_label = st.selectbox("Choose an item to edit:", labels)
        selected_index = labels.index(selected_label)
        item = data["items"][selected_index]

        # Helper to initialize session_state defaults for edit widgets
        def get_ss(key, default):
            if key not in st.session_state:
                st.session_state[key] = default
            return st.session_state[key]

        base_key = f"edit_{selected_index}_"

        name_key = base_key + "name"
        url_key = base_key + "url"
        cat_key = base_key + "cat"
        prio_key = base_key + "prio"
        size_key = base_key + "size"
        style_key = base_key + "style"
        price_key = base_key + "price"
        purchased_key = base_key + "purchased"

        # Defaults
        default_price_str = ""
        if item.get("price") is not None:
            try:
                default_price_str = f"{float(item['price']):.2f}"
            except Exception:
                default_price_str = str(item["price"])

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Item name:",
                value=get_ss(name_key, item.get("name", "")),
                key=name_key,
            )
            url = st.text_input(
                "Item URL:",
                value=get_ss(url_key, item.get("url", "")),
                key=url_key,
            )
            category = st.selectbox(
                "Category:",
                CATEGORIES,
                index=(
                    CATEGORIES.index(item.get("category", "Misc"))
                    if item.get("category") in CATEGORIES
                    else 0
                ),
                key=cat_key,
            )
            priority = st.selectbox(
                "Priority:",
                ["High", "Medium", "Low"],
                index=(
                    ["High", "Medium", "Low"].index(item.get("priority", "High"))
                    if item.get("priority") in ["High", "Medium", "Low"]
                    else 0
                ),
                key=prio_key,
            )

        with col2:
            size = st.text_input(
                "Size (e.g. 10.5, M, 34x30):",
                value=get_ss(size_key, item.get("size", "")),
                key=size_key,
            )
            style = st.text_input(
                "Style / Color:",
                value=get_ss(style_key, item.get("style", "")),
                key=style_key,
            )
            price_str = st.text_input(
                "Price (e.g. 129.99):",
                value=get_ss(price_key, default_price_str),
                key=price_key,
            )
            purchased_flag = st.checkbox(
                "Purchased?",
                value=get_ss(purchased_key, item.get("purchased", False)),
                key=purchased_key,
            )

        st.write("Update image (optional):")
        uploaded_file_edit = st.file_uploader(
            "New image (PNG/JPG). Leave blank to keep current.",
            type=["png", "jpg", "jpeg"],
            key=f"edit_img_{selected_index}",
        )

        if st.button("Save Changes", key=f"save_edit_{selected_index}"):
            if not name.strip():
                st.error("Item name cannot be empty.")
                st.stop()

            if not url.strip():
                st.error("Item URL cannot be empty.")
                st.stop()

            price_val, price_err = parse_price_to_float(price_str)
            if price_err:
                st.error(price_err)
                st.stop()

            # Apply changes to the item
            item["name"] = name.strip()
            item["url"] = url.strip()
            item["category"] = category
            item["priority"] = priority
            item["size"] = size.strip()
            item["style"] = style.strip()
            item["purchased"] = bool(purchased_flag)
            item["price"] = price_val

            # Update image only if new one uploaded
            if uploaded_file_edit is not None:
                item["image"] = file_to_base64(uploaded_file_edit)

            # Persist to archive by URL as well
            data["archive"][item["url"]] = item.copy()

            save_data(data)
            st.success("Item updated!")
            st.rerun()
