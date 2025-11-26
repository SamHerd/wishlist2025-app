import streamlit as st
import json
import base64
from pathlib import Path

JSON_PATH = "wishlist.json"

# ---------------------------------------------------
# Load + Save JSON (with archive support)
# ---------------------------------------------------
def load_data():
    p = Path(JSON_PATH)
    if not p.exists():
        return {"preferences": {}, "items": [], "archive": {}}

    with open(JSON_PATH, "r") as f:
        data = json.load(f)

    if "preferences" not in data:
        data["preferences"] = {}
    if "items" not in data:
        data["items"] = []
    if "archive" not in data:
        data["archive"] = {}

    return data


def save_data(data):
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------
# Convert uploaded file → Base64 string
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


def parse_price_to_float(text):
    if not text or not text.strip():
        return None, None

    raw = text.strip()
    cleaned = raw.replace("$", "").replace(",", "").strip()

    try:
        return float(cleaned), None
    except ValueError:
        return None, f"Could not understand price: '{raw}'. Use something like 129.99 or $129.99."


# ---------------------------------------------------
# Streamlit UI Setup
# ---------------------------------------------------
st.set_page_config(page_title="Sam's Wishlist", layout="wide")
data = load_data()

st.title("🎁 Sam’s 2025 Christmas Wishlist")

# ---------------------------------------------------
# Cyber Christmas Banner (correct size + cropped cleanly)
# ---------------------------------------------------
if Path("christmas_banner.jpg").exists():

    # Assign a special CSS class ONLY to this banner
    st.markdown(
        """
        <style>
        .banner-img {
            width: 100% !important;
            max-height: 260px !important;    /* Adjust to taste */
            object-fit: cover !important;    /* Auto-crops top/bottom */
            border-radius: 10px !important;
            box-shadow: 0 0 18px rgba(0,255,180,0.35); /* neon glow */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f'<img src="christmas_banner.jpg" class="banner-img">',
        unsafe_allow_html=True
    )

else:
    st.markdown("### 🎄 (christmas_banner.jpg not found — upload it to your repo)")


# ---------------------------------------------------
# Predefined categories
# ---------------------------------------------------
CATEGORIES = [
    "Shoes", "Jacket", "Shirts", "Outerwear", "Menswear",
    "Graphic Tee", "Toys", "UNT Merch", "Amazon", "Misc"
]

# ---------------------------------------------------
# Tabs: View Wishlist FIRST (default), Add Item SECOND
# ---------------------------------------------------
tabs = st.tabs(["📜 View Wishlist", "➕ Add a New Item"])
tab_view = tabs[0]
tab_add = tabs[1]

# ---------------------------------------------------
# TAB 1: VIEW WISHLIST (now default)
# ---------------------------------------------------
with tab_view:
    st.header("Your Wishlist")

    filter_cat = st.multiselect("Filter by category:", CATEGORIES)
    filter_priority = st.multiselect("Filter by priority:", ["High", "Medium", "Low"])

    col_min, col_max = st.columns(2)
    with col_min:
        min_price_str = st.text_input("Min price (optional):", key="min_price_filter")
    with col_max:
        max_price_str = st.text_input("Max price (optional):", key="max_price_filter")

    search = st.text_input("Search items by name:", key="search_filter")

    filtered = list(data["items"])

    if filter_cat:
        filtered = [i for i in filtered if i.get("category") in filter_cat]

    if filter_priority:
        filtered = [i for i in filtered if i.get("priority") in filter_priority]

    min_price_val, _ = parse_price_to_float(min_price_str) if min_price_str.strip() else (None, None)
    max_price_val, _ = parse_price_to_float(max_price_str) if max_price_str.strip() else (None, None)

    if min_price_val is not None:
        filtered = [i for i in filtered if i.get("price") is not None and i["price"] >= min_price_val]

    if max_price_val is not None:
        filtered = [i for i in filtered if i.get("price") is not None and i["price"] <= max_price_val]

    if search.strip():
        s = search.lower()
        filtered = [i for i in filtered if s in i.get("name", "").lower()]

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
                st.write(f"**Price:** ${item['price']:,.2f}")

            if item.get("url"):
                st.write(f"[View Item]({item['url']})")

            purchased_flag = st.checkbox(
                "Purchased?",
                value=item.get("purchased", False),
                key=f"purchased_{idx}"
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
# TAB 2: ADD ITEM
# ---------------------------------------------------
with tab_add:
    st.header("Add a New Item")

    new_url = st.text_input("Item URL:")

    archive_entry = data["archive"].get(new_url, {}) if new_url else {}

    auto_name = archive_entry.get("name", "")
    auto_cat = archive_entry.get("category", "Misc")
    auto_img = archive_entry.get("image", "")
    auto_size = archive_entry.get("size", "")
    auto_style = archive_entry.get("style", "")
    auto_price_val = archive_entry.get("price", None)

    auto_price_str = f"{auto_price_val:.2f}" if auto_price_val is not None else ""

    uploaded_file = st.file_uploader("Upload item image (PNG/JPG)", type=["png", "jpg", "jpeg"])

    name = st.text_input("Item name:", auto_name)
    category = st.selectbox("Category:", CATEGORIES,
                            index=CATEGORIES.index(auto_cat) if auto_cat in CATEGORIES else 0)
    priority = st.selectbox("Priority:", ["High", "Medium", "Low"])

    size = st.text_input("Size (e.g. 10.5, L, 34x30):", auto_size)
    style = st.text_input("Style / Color (e.g. taupe, dark green):", auto_style)
    price_str = st.text_input("Price (e.g. 129.99 or $129.99):", auto_price_str)

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

