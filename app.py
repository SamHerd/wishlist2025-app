import streamlit as st
import json
import base64
from pathlib import Path

# ---------------------------------------------------
# CONSTANTS
# ---------------------------------------------------
JSON_PATH = "wishlist.json"
RAW_BANNER_URL = (
    "https://raw.githubusercontent.com/SamHerd/wishlist2025-app/main/christmas_banner.jpg"
)

# ---------------------------------------------------
# LOAD/SAVE JSON
# ---------------------------------------------------
def load_data():
    p = Path(JSON_PATH)
    if not p.exists():
        return {"preferences": {}, "items": [], "archive": {}}

    with open(JSON_PATH, "r") as f:
        data = json.load(f)

    data.setdefault("preferences", {})
    data.setdefault("items", [])
    data.setdefault("archive", {})

    return data


def save_data(data):
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------
# IMAGE HELPERS
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
# PRICE PARSER
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
# STREAMLIT SETUP
# ---------------------------------------------------
st.set_page_config(page_title="Sam's Wishlist", layout="wide")
data = load_data()

# ---------------------------------------------------
# GLOBAL STYLES (ZERO TOP SPACE + BLUE BG + SNOW)
# ---------------------------------------------------
st.markdown("""
<style>

    /* Remove ALL default padding/margins/headers */
    header, [data-testid="stHeader"], [data-testid="stAppHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    [data-testid="stAppViewContainer"],
    .main, .block-container {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Solid icy blue background */
    html, body, .stApp {
        background: #e6f5ff !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow-x: hidden !important;
    }

    /* Snowflake style */
    .snowflake {
        position: fixed;
        top: -10px;
        font-size: 18px;
        color: rgba(255,255,255,0.95);
        user-select: none;
        pointer-events: none;
        z-index: 1;
        animation: fall linear infinite;
    }

    @keyframes fall {
        0%   { transform: translateY(0) translateX(0); opacity: 1; }
        100% { transform: translateY(110vh) translateX(-40px); opacity: 0; }
    }

""" + "\n".join([
    f".flake{n} {{ left: {n * 2.5}%; animation-duration: {5 + (n % 4)}s; }}"
    for n in range(40)
]) + """

    /* Banner (extended height) */
    img.banner-img {
        width: 100% !important;
        height: 600px !important;
        max-height: 600px !important;
        object-fit: cover !important;
        object-position: center top !important;
        border-radius: 10px !important;
        box-shadow: 0 0 20px rgba(0,255,200,0.35);
        margin-top: 0 !important;
    }

    /* Neon titles */
    h1, h2, h3 {
        font-weight: 900 !important;
        color: #0a3d4f !important;
        text-shadow: 0 0 8px rgba(0,255,200,0.35),
                     0 0 14px rgba(0,255,200,0.25);
    }

</style>
""", unsafe_allow_html=True)

# Snowflakes injected
for n in range(40):
    st.markdown(f'<div class="snowflake flake{n}">❄</div>', unsafe_allow_html=True)


# ---------------------------------------------------
# TITLE + BANNER (AT THE VERY TOP NOW)
# ---------------------------------------------------
st.title("🎁 Sam’s 2025 Christmas Wishlist")

st.markdown(
    f'<img src="{RAW_BANNER_URL}" class="banner-img">',
    unsafe_allow_html=True
)


# ---------------------------------------------------
# CATEGORIES
# ---------------------------------------------------
CATEGORIES = [
    "Shoes", "Jacket", "Shirts", "Outerwear", "Menswear",
    "Graphic Tee", "Toys", "UNT Merch", "Amazon", "Misc"
]


# ---------------------------------------------------
# TABS (VIEW FIRST)
# ---------------------------------------------------
tab_view, tab_add = st.tabs(["📜 View Wishlist", "➕ Add a New Item"])


# ---------------------------------------------------
# TAB 1 — VIEW
# ---------------------------------------------------
with tab_view:

    st.header("View Sam’s Wishlist")
    st.write("<hr>", unsafe_allow_html=True)

    filter_cat = st.multiselect("Filter by category:", CATEGORIES)
    filter_priority = st.multiselect("Filter by priority:", ["High", "Medium", "Low"])

    col_min, col_max = st.columns(2)
    min_price_str = col_min.text_input("Min price (optional):")
    max_price_str = col_max.text_input("Max price (optional):")

    search = st.text_input("Search items by name:")

    filtered = list(data["items"])

    if filter_cat:
        filtered = [i for i in filtered if i.get("category") in filter_cat]

    if filter_priority:
        filtered = [i for i in filtered if i.get("priority") in filter_priority]

    min_price_val, _ = parse_price_to_float(min_price_str) if min_price_str else (None, None)
    max_price_val, _ = parse_price_to_float(max_price_str) if max_price_str else (None, None)

    if min_price_val is not None:
        filtered = [i for i in filtered if i.get("price") and i["price"] >= min_price_val]
    if max_price_val is not None:
        filtered = [i for i in filtered if i.get("price") and i["price"] <= max_price_val]

    if search.strip():
        s = search.lower()
        filtered = [i for i in filtered if s in i.get("name", "").lower()]

    cols = st.columns(2)

    for idx, item in enumerate(filtered):
        with cols[idx % 2]:
            st.write("---")
            show_base64_image(item.get("image"))
            st.subheader(item.get("name", "(no name)"))
            st.write(f"**Category:** {item.get('category')}")
            st.write(f"**Priority:** {item.get('priority')}")
            if item.get("size"):
                st.write(f"**Size:** {item['size']}")
            if item.get("style"):
                st.write(f"**Style/Color:** {item['style']}")
            if item.get("price"):
                st.write(f"**Price:** ${item['price']:,.2f}")
            if item.get("url"):
                st.write(f"[View Item]({item['url']})")

            purchased_flag = st.checkbox(
                "Purchased?",
                value=item.get("purchased", False),
                key=f"purchased_{idx}"
            )
            if purchased_flag != item.get("purchased"):
                item["purchased"] = purchased_flag
                save_data(data)

            if st.button("❌ Remove", key=f"rm_{idx}"):
                data["items"].remove(item)
                save_data(data)
                st.rerun()


# ---------------------------------------------------
# TAB 2 — ADD
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
    auto_price_val = archive_entry.get("price")

    auto_price_str = f"{auto_price_val:.2f}" if auto_price_val else ""

    uploaded_file = st.file_uploader("Upload item image (PNG/JPG)", type=["png", "jpg", "jpeg"])

    name = st.text_input("Item name:", auto_name)
    category = st.selectbox("Category:", CATEGORIES, index=CATEGORIES.index(auto_cat))
    priority = st.selectbox("Priority:", ["High", "Medium", "Low"])

    size = st.text_input("Size:", auto_size)
    style = st.text_input("Style / Color:", auto_style)
    price_str = st.text_input("Price:", auto_price_str)

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
            "price": price_val
        }

        data["items"].append(item)
        data["archive"][new_url] = item.copy()

        save_data(data)
        st.success("Item added!")
        st.rerun()
