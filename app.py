import streamlit as st
import json
import base64
from pathlib import Path

JSON_PATH = "wishlist.json"

RAW_BANNER_URL = (
    "https://raw.githubusercontent.com/SamHerd/wishlist2025-app/main/christmas_banner.jpg"
)

# ---------------------------------------------------
# Load + Save JSON
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
# Base64 tools
# ---------------------------------------------------
def file_to_base64(file):
    if not file:
        return ""
    return base64.b64encode(file.read()).decode()

def show_img(b64):
    if b64:
        st.image(base64.b64decode(b64), use_column_width=False)
    else:
        st.write("(no image)")

# ---------------------------------------------------
# Price helper
# ---------------------------------------------------
def parse_price_to_float(text):
    if not text or not text.strip():
        return None, None
    cleaned = text.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned), None
    except:
        return None, f"Could not understand price: '{text}'. Use 129.99 or $129.99."

# ---------------------------------------------------
# Page Setup
# ---------------------------------------------------
st.set_page_config(page_title="Sam's Wishlist", layout="wide")
data = load_data()

# ---------------------------------------------------
# SAFE + WORKING BACKGROUND + SNOW
# ---------------------------------------------------
st.markdown(
    """
<style>

html, body, .stApp {
    background: #ddecf7;
    background-image:
        radial-gradient(circle, rgba(255,255,255,0.8) 0 2px, transparent 2px),
        radial-gradient(circle at 20% 80%, rgba(255,255,255,0.7) 0 2px, transparent 2px),
        radial-gradient(circle at 80% 20%, rgba(255,255,255,0.7) 0 2px, transparent 2px),
        linear-gradient(180deg, #e7f3ff 0%, #d8eafb 40%, #e7f3ff 100%);
    background-size: 260px 260px, 260px 260px, 260px 260px, cover;
}

/* Falling snow — stable version */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        radial-gradient(circle, rgba(255,255,255,0.8) 0 2px, transparent 2px),
        radial-gradient(circle, rgba(255,255,255,0.5) 0 1.5px, transparent 1.5px);
    background-size: 200px 200px, 260px 260px;
    animation: snowFall 35s linear infinite;
    opacity: 0.8;
    z-index: 1;
}

@keyframes snowFall {
    0% { background-position: 0 -200px, 0 0; }
    100% { background-position: 0 800px, 0 900px; }
}

/* Candy cane title */
h1.app-title, h2.section-title {
    font-weight: 800;
    background-image: repeating-linear-gradient(
        135deg, 
        #ffffff 0 8px,
        #ff6b81 8px 14px,
        #b8fff1 14px 20px
    );
    -webkit-background-clip: text;
    color: transparent;
    text-shadow: 0 0 6px rgba(0,0,0,0.25);
}

/* Banner style */
img.banner-img {
    width: 100%;
    margin-top: 0.5rem;
    border-radius: 10px;
    box-shadow: 0 0 18px rgba(0,255,180,0.35);
    object-fit: cover;
    max-height: 400px;
}

.block-container {
    margin-top: 0 !important;
    padding-top: 1rem !important;
    position: relative;
    z-index: 2;  /* above snow */
}

</style>
""",
    unsafe_allow_html=True
)

# ---------------------------------------------------
# Title + Banner
# ---------------------------------------------------
st.markdown('<h1 class="app-title">🎁 Sam’s 2025 Christmas Wishlist</h1>', unsafe_allow_html=True)
st.markdown(f'<img src="{RAW_BANNER_URL}" class="banner-img">', unsafe_allow_html=True)

# ---------------------------------------------------
# Categories
# ---------------------------------------------------
CATEGORIES = [
    "Shoes", "Jacket", "Shirts", "Outerwear", "Menswear",
    "Graphic Tee", "Toys", "UNT Merch", "Amazon", "Misc"
]

# ---------------------------------------------------
# Tabs
# ---------------------------------------------------
tabs = st.tabs(["📜 View Wishlist", "➕ Add a New Item"])
tab_view, tab_add = tabs

# ---------------------------------------------------
# VIEW TAB
# ---------------------------------------------------
with tab_view:
    st.markdown('<h2 class="section-title">View Sam’s Wishlist</h2>', unsafe_allow_html=True)
    st.write("<hr>", unsafe_allow_html=True)

    # Filters
    filter_cat = st.multiselect("Filter by category:", CATEGORIES)
    filter_priority = st.multiselect("Filter by priority:", ["High", "Medium", "Low"])

    col_min, col_max = st.columns(2)
    with col_min:
        min_price_str = st.text_input("Min price:")
    with col_max:
        max_price_str = st.text_input("Max price:")

    search = st.text_input("Search by name:")

    filtered = list(data["items"])

    # Apply filters
    if filter_cat:
        filtered = [i for i in filtered if i.get("category") in filter_cat]
    if filter_priority:
        filtered = [i for i in filtered if i.get("priority") in filter_priority]

    min_val, _ = parse_price_to_float(min_price_str) if min_price_str else (None, None)
    max_val, _ = parse_price_to_float(max_price_str) if max_price_str else (None, None)

    if min_val is not None:
        filtered = [i for i in filtered if i.get("price") and i["price"] >= min_val]
    if max_val is not None:
        filtered = [i for i in filtered if i.get("price") and i["price"] <= max_val]

    if search.strip():
        s = search.lower()
        filtered = [i for i in filtered if s in i.get("name", "").lower()]

    cols = st.columns(2)
    for idx, item in enumerate(filtered):
        with cols[idx % 2]:
            st.write("---")
            show_img(item.get("image",""))
            st.subheader(item.get("name","(no name)"))
            st.write(f"**Category:** {item.get('category','N/A')}")
            st.write(f"**Priority:** {item.get('priority','N/A')}")
            if item.get("size"): st.write(f"**Size:** {item['size']}")
            if item.get("style"): st.write(f"**Style:** {item['style']}")
            if item.get("price") is not None:
                st.write(f"**Price:** ${item['price']:,.2f}")
            if item.get("url"):
                st.write(f"[Open Link]({item['url']})")

            purchased = st.checkbox("Purchased?", item.get("purchased", False), key=f"p_{idx}")
            if purchased != item.get("purchased", False):
                item["purchased"] = purchased
                save_data(data)

            if st.button("❌ Remove", key=f"rm_{idx}"):
                data["items"].remove(item)
                save_data(data)
                st.rerun()

# ---------------------------------------------------
# ADD TAB
# ---------------------------------------------------
with tab_add:
    st.markdown('<h2 class="section-title">Add a New Item</h2>', unsafe_allow_html=True)
    st.write("<hr>", unsafe_allow_html=True)

    new_url = st.text_input("Item URL:")
    auto = data["archive"].get(new_url, {}) if new_url else {}

    uploaded = st.file_uploader("Upload item image", type=["png","jpg","jpeg"])

    name = st.text_input("Item name:", auto.get("name",""))
    category = st.selectbox("Category:", CATEGORIES, index=CATEGORIES.index(auto.get("category","Misc")) if auto.get("category") in CATEGORIES else 0)
    priority = st.selectbox("Priority:", ["High","Medium","Low"])
    size = st.text_input("Size:", auto.get("size",""))
    style = st.text_input("Style / Color:", auto.get("style",""))
    price_str = st.text_input("Price:", f"{auto.get('price', '')}")

    if st.button("Add Item"):
        if not new_url.strip():
            st.error("URL required.")
            st.stop()
        if not name.strip():
            st.error("Name required.")
            st.stop()

        price_val, err = parse_price_to_float(price_str)
        if err:
            st.error(err)
            st.stop()

        img_b64 = file_to_base64(uploaded) if uploaded else auto.get("image","")

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
        st.success("Added!")
        st.rerun()
