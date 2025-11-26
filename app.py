import streamlit as st
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import urllib.parse

st.markdown("## 🔥 ScraperAPI Enabled Version 🔥")

JSON_PATH = "wishlist.json"

# =============================
# Load / Save Data
# =============================
def load_data():
    path = Path(JSON_PATH)
    if not path.exists():
        return {"preferences": {}, "items": []}

    with open(path, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        data = {"preferences": {}, "items": data}

    data.setdefault("preferences", {})
    data.setdefault("items", [])
    return data


def save_data(data):
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)


# =============================
# Utilities
# =============================
def clean_title(t):
    if not t:
        return "Unknown Item"
    t = t.replace("\n", " ").strip()
    t = " ".join(t.split())
    return t[:140]


def detect_category(url, title):
    u = url.lower()
    t = title.lower()

    if "nike" in u: return "Shoes"
    if "north-face" in u or "thenorthface" in u: return "Jacket"
    if "carhartt" in u: return "Outerwear"
    if "macys" in u: return "Shirts"
    if "menswearhouse" in u: return "Menswear"
    if "pacsun" in u: return "Graphic Tee"
    if "unt" in u or "north texas" in t: return "UNT Merch"
    if "amazon" in u and ("lego" in u or "puzzle" in t): return "Toys"
    if "amazon" in u: return "Amazon"
    return "Misc"


def scrape_image_from_html(soup):
    # OpenGraph
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og.get("content")

    # Twitter Card
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        return tw.get("content")

    # Fallback: first <img>
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith("http"):
            return src

    return ""


# =============================
# Scrape via ScraperAPI
# =============================
def scrape_item(url: str):
    try:
        api_key = st.secrets.scraperapi.api_key
        encoded_url = urllib.parse.quote(url, safe="")

        full_url = (
            f"https://api.scraperapi.com/"
            f"?api_key={api_key}"
            f"&render=true"
            f"&premium=true"
            f"&keep_headers=true"
            f"&url={encoded_url}"
        )

        r = requests.get(full_url, timeout=30)
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # Get title
        raw_title = soup.find("title").text if soup.find("title") else "Unknown Item"
        title = clean_title(raw_title)

        # Get image
        img = scrape_image_from_html(soup)

        # If still no image, try common JS-rendered selectors
        if not img:
            # MensWearhouse primary product image selectors
            sel = soup.select_one("img.primary-image, img#main-image, img.product-image")
            if sel and sel.get("src"):
                img = sel["src"]

        category = detect_category(url, title)
        return title, img, category

    except Exception:
        return "Unknown Item", "", "Misc"


# =============================
# Streamlit Setup
# =============================
st.set_page_config(page_title="Sam's Wishlist", layout="wide")
data = load_data()

# Dark Mode
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("""
        <style>
        body, .stApp { background-color:#1a1a1a !important; color:white !important; }
        .stButton button { background-color:#333 !important; color:white !important; }
        </style>
    """, unsafe_allow_html=True)

st.title("🎁 Sam’s 2025 Wishlist (ScraperAPI Edition)")


# =============================
# Preferences Section
# =============================
st.header("Your Preferences")

prefs = data["preferences"]

shirt_size  = st.text_input("Shirt size:",  prefs.get("shirt_size", ""))
jacket_size = st.text_input("Jacket size:", prefs.get("jacket_size", ""))
pants_size  = st.text_input("Pants size:",  prefs.get("pants_size", ""))
shoe_size   = st.text_input("Shoe size:",   prefs.get("shoe_size", ""))
styles      = st.text_input("Preferred colors/styles:", prefs.get("styles", ""))

if st.button("Save Preferences"):
    prefs.update({
        "shirt_size": shirt_size,
        "jacket_size": jacket_size,
        "pants_size": pants_size,
        "shoe_size": shoe_size,
        "styles": styles,
    })
    save_data(data)
    st.success("Saved!")


# =============================
# Add Item
# =============================
st.header("Add a New Item")

new_url = st.text_input("Item URL:")
priority = st.selectbox("Priority:", ["High", "Medium", "Low"])

if st.button("Add Item"):
    with st.spinner("Scraping item via ScraperAPI…"):
        title, img, auto_cat = scrape_item(new_url)

    item = {
        "name": title,
        "url": new_url,
        "image": img,
        "category": auto_cat,
        "priority": priority,
        "purchased": False
    }

    data["items"].append(item)
    save_data(data)
    st.success("Item added!")
    st.rerun()


# =============================
# Filters
# =============================
st.header("Your Wishlist")

all_categories = sorted({i["category"] for i in data["items"]})
filter_cat = st.multiselect("Filter by category:", all_categories)
filter_priority = st.multiselect("Filter by priority:", ["High", "Medium", "Low"])
search = st.text_input("Search items:")

filtered = data["items"]

if filter_cat:
    filtered = [i for i in filtered if i["category"] in filter_cat]
if filter_priority:
    filtered = [i for i in filtered if i["priority"] in filter_priority]
if search:
    filtered = [i for i in filtered if search.lower() in i["name"].lower()]


# =============================
# Display Items
# =============================
cols = st.columns(2)

for idx, item in enumerate(filtered):
    with cols[idx % 2]:
        with st.container():
            if item.get("image"):
                st.image(item["image"], width=260)
            else:
                st.write("(no image)")

            st.subheader(item["name"])
            st.write(f"**Category:** {item['category']}")
            st.write(f"**Priority:** {item['priority']}")
            st.write(f"[View Item]({item['url']})")

            # Manual override image URL
            new_img = st.text_input(
                "Image URL (optional)",
                value=item.get("image", ""),
                key=f"img_{idx}"
            )
            if new_img != item.get("image"):
                item["image"] = new_img
                save_data(data)
                st.success("Updated image!")
                st.rerun()

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
                st.warning("Removed.")
                st.rerun()

