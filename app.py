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

    # safety checks
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


# Base64 → displayed image
def show_base64_image(b64_str):
    if not b64_str:
        st.write("(no image)")
        return
    st.image(base64.b64decode(b64_str), use_column_width=False)


# ---------------------------------------------------
# Streamlit UI Setup
# ---------------------------------------------------
st.set_page_config(page_title="Sam's Wishlist", layout="wide")
data = load_data()

st.title("🎁 Sam’s 2025 Christmas Wishlist")


# ---------------------------------------------------
# Preferences
# ---------------------------------------------------
st.header("Your Preferences")
prefs = data["preferences"]

shirt = st.text_input("Shirt size:", prefs.get("shirt_size", ""))
jacket = st.text_input("Jacket size:", prefs.get("jacket_size", ""))
pants = st.text_input("Pants size:", prefs.get("pants_size", ""))
shoes = st.text_input("Shoe size:", prefs.get("shoe_size", ""))
styles = st.text_input("Preferred colors/styles:", prefs.get("styles", ""))

if st.button("Save Preferences"):
    prefs["shirt_size"] = shirt
    prefs["jacket_size"] = jacket
    prefs["pants_size"] = pants
    prefs["shoe_size"] = shoes
    prefs["styles"] = styles
    data["preferences"] = prefs
    save_data(data)
    st.success("Saved!")


# ---------------------------------------------------
# Predefined categories
# ---------------------------------------------------
CATEGORIES = [
    "Shoes", "Jacket", "Shirts", "Outerwear", "Menswear",
    "Graphic Tee", "Toys", "UNT Merch", "Amazon", "Misc"
]


# ---------------------------------------------------
# ADD ITEM
# ---------------------------------------------------
st.header("Add a New Item")

new_url = st.text_input("Item URL:")
uploaded_file = st.file_uploader("Upload item image (PNG/JPG)", type=["png", "jpg", "jpeg"])

# Auto-fill name/category from archive
auto_name = ""
auto_cat = "Misc"
auto_img = ""

if new_url in data["archive"]:
    prev = data["archive"][new_url]
    auto_name = prev.get("name", "")
    auto_cat = prev.get("category", "Misc")
    auto_img = prev.get("image", "")

name = st.text_input("Item name:", auto_name)
category = st.selectbox("Category:", CATEGORIES, index=CATEGORIES.index(auto_cat) if auto_cat in CATEGORIES else 0)
priority = st.selectbox("Priority:", ["High", "Medium", "Low"])

if st.button("Add Item"):
    # Convert uploaded or fallback to archived image
    if uploaded_file:
        img_b64 = file_to_base64(uploaded_file)
    else:
        img_b64 = auto_img

    item = {
        "name": name,
        "url": new_url,
        "image": img_b64,
        "category": category,
        "priority": priority,
        "purchased": False
    }

    # Save to current list
    data["items"].append(item)

    # Save to archive for future reuse
    data["archive"][new_url] = {
        "name": name,
        "category": category,
        "image": img_b64
    }

    save_data(data)
    st.success("Item added!")
    st.rerun()


# ---------------------------------------------------
# FILTERS
# ---------------------------------------------------
st.header("Your Wishlist")

filter_cat = st.multiselect("Filter by category:", CATEGORIES)
filter_priority = st.multiselect("Filter by priority:", ["High", "Medium", "Low"])
search = st.text_input("Search items:")

filtered = data["items"]

if filter_cat:
    filtered = [i for i in filtered if i["category"] in filter_cat]

if filter_priority:
    filtered = [i for i in filtered if i["priority"] in filter_priority]

if search.strip():
    filtered = [i for i in filtered if search.lower() in i["name"].lower()]


# ---------------------------------------------------
# DISPLAY ITEMS (2-column layout)
# ---------------------------------------------------
cols = st.columns(2)

for idx, item in enumerate(filtered):
    with cols[idx % 2]:
        st.write("---")

        # Show image from Base64
        show_base64_image(item["image"])

        st.subheader(item["name"])
        st.write(f"**Category:** {item['category']}")
        st.write(f"**Priority:** {item['priority']}")
        st.write(f"[View Item]({item['url']})")

        # Purchased toggle
        purchased_flag = st.checkbox(
            "Purchased?",
            value=item.get("purchased", False),
            key=f"purchased_{idx}"
        )
        if purchased_flag != item.get("purchased", False):
            item["purchased"] = purchased_flag
            save_data(data)

        # Remove button
        if st.button("❌ Remove", key=f"rm_{idx}"):
            data["items"].remove(item)
            save_data(data)
            st.warning("Removed.")
            st.rerun()

