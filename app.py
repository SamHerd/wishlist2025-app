import streamlit as st
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

st.markdown("## 🔥 NEW VERSION LOADED 🔥")

JSON_PATH = "wishlist.json"

# =============================
# Helpers
# =============================
def load_data():
    path = Path(JSON_PATH)
    if not path.exists():
        return {"preferences": {}, "items": []}

    with open(path, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        return {"preferences": {}, "items": data}

    data.setdefault("preferences", {})
    data.setdefault("items", [])
    return data


def save_data(data):
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)


def clean_title(t):
    if not t:
        return "Unknown Item"
    t = t.replace("\n", " ").strip()
    return " ".join(t.split())[:120]


def detect_category(url, title):
    u = url.lower()
    t = title.lower()

    if "nike" in u:
        return "Shoes"
    if "north-face" in u or "thenorthface" in u:
        return "Jacket"
    if "carhartt" in u:
        return "Outerwear"
    if "macys" in u:
        return "Shirts"
    if "menswearhouse" in u:
        return "Menswear"
    if "pacsun" in u:
        return "Graphic Tee"
    if "amazon" in u and ("lego" in u or "puzzle" in t):
        return "Toys"
    if "unt" in u or "north texas" in t:
        return "UNT Merch"
    if "amazon" in u:
        return "Amazon"
    return "Misc"


# =============================
# Scraper Utilities
# =============================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def normalize_image_url(url):
    """Ensures URL is valid HTTPS."""
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return "https://" + url.lstrip("/")
    return url


def scrape_image(soup):
    # opengraph -> twitter -> img fallback
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return normalize_image_url(og["content"])

    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        return normalize_image_url(tw["content"])

    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith(("http", "//")):
            return normalize_image_url(src)

    return ""


# =============================
# Main Scraper
# =============================
def scrape_item(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        html = r.text

        # ----- BLOCKED PAGE HANDLING -----
        if "Access Denied" in html or "deny" in html.lower():
            return "Access Denied", "", detect_category(url, "Access Denied")

        soup = BeautifulSoup(html, "html.parser")

        # ----- NIKE SPECIAL CASE -----
        if "nike.com" in url.lower():
            try:
                script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
                if script_tag:
                    data_json = json.loads(script_tag.text)
                    product = (
                        data_json.get("props", {})
                        .get("pageProps", {})
                        .get("product", {})
                    )

                    title = clean_title(
                        product.get("title")
                        or product.get("subtitle")
                        or "Nike Item"
                    )

                    images = product.get("images", [])
                    image_url = ""

                    if images:
                        img0 = images[0]
                        for key in ["portraitURL", "squarishURL", "fullSizeURL", "url", "imageUrl"]:
                            if img0.get(key):
                                image_url = normalize_image_url(img0[key])
                                break

                    return title, image_url, detect_category(url, title)
            except Exception:
                pass  # fallback below

        # ----- GENERIC SCRAPER -----
        title_tag = soup.find("title")
        title = clean_title(title_tag.text if title_tag else "Unknown Item")

        img = scrape_image(soup)
        cat = detect_category(url, title)

        return title, img, cat

    except Exception:
        return "Unknown Item", "", "Misc"


# =============================
# Streamlit Setup
# =============================
st.set_page_config(page_title="Sam's Wishlist", layout="wide")
data = load_data()

theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>
        body, .stApp { background-color:#1a1a1a !important; color:white !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title("🎁 Sam’s 2025 Wishlist")


# =============================
# Preferences
# =============================
st.header("Your Preferences")
prefs = data["preferences"]

shirt_size = st.text_input("Shirt size:", prefs.get("shirt_size", ""))
jacket_size = st.text_input("Jacket size:", prefs.get("jacket_size", ""))
pants_size = st.text_input("Pants size:", prefs.get("pants_size", ""))
shoe_size = st.text_input("Shoe size:", prefs.get("shoe_size", ""))
styles = st.text_input("Preferred colors/styles:", prefs.get("styles", ""))

if st.button("Save Preferences"):
    prefs.update(
        shirt_size=shirt_size,
        jacket_size=jacket_size,
        pants_size=pants_size,
        shoe_size=shoe_size,
        styles=styles,
    )
    save_data(data)
    st.success("Saved!")


# =============================
# Add Item
# =============================
st.header("Add a New Item")
new_url = st.text_input("Item URL:")
priority = st.selectbox("Priority:", ["High", "Medium", "Low"])

if st.button("Add Item"):
    with st.spinner("Scraping item…"):
        title, img, auto_cat = scrape_item(new_url)

    data["items"].append(
        {
            "name": title,
            "url": new_url,
            "image": img,
            "category": auto_cat,
            "priority": priority,
            "purchased": False,
        }
    )
    save_data(data)
    st.success("Item added!")
    st.rerun()


# =============================
# Filters
# =============================
st.header("Your Wishlist")
items = data["items"]

all_categories = sorted({i["category"] for i in items}) if items else []
filter_cat = st.multiselect("Filter by category:", all_categories)
filter_priority = st.multiselect("Filter by priority:", ["High", "Medium", "Low"])
search = st.text_input("Search items:")

filtered = list(items)

if filter_cat:
    filtered = [i for i in filtered if i["category"] in filter_cat]
if filter_priority:
    filtered = [i for i in filtered if i["priority"] in filter_priority]
if search.strip():
    filtered = [i for i in filtered if search.lower() in i["name"].lower()]


# =============================
# Display Items
# =============================
cols = st.columns(2)

for idx, item in enumerate(filtered):
    with cols[idx % 2]:
        st.container()
        if item.get("image"):
            st.image(item["image"], width=260)
        else:
            st.write("(no image)")

        st.subheader(item["name"])
        st.write(f"**Category:** {item['category']}")
        st.write(f"**Priority:** {item['priority']}")
        st.write(f"[View Item]({item['url']})")

        img_override = st.text_input(
            "Image URL (optional)",
            value=item.get("image", ""),
            key=f"img_{idx}",
        )
        if img_override != item.get("image", ""):
            item["image"] = img_override
            save_data(data)
            st.success("Updated!")
            st.rerun()

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
            st.warning("Removed!")
            st.rerun()
