import streamlit as st
import json
import requests
from bs4 import BeautifulSoup

JSON_PATH = "wishlist.json"


# =============================
# Helpers
# =============================
def load_data():
    with open(JSON_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)

def clean_title(t):
    if not t:
        return "Unknown Item"
    t = t.replace("\n", " ").strip()
    t = " ".join(t.split())     # collapse repeated spaces
    return t[:120]


def detect_category(url, title):
    u = url.lower()
    t = title.lower()

    if "nike" in u: return "Shoes"
    if "north-face" in u or "thenorthface" in u: return "Jacket"
    if "amazon" in u and ("lego" in u or "puzzle" in t): return "Toys"
    if "unt" in u or "north texas" in t: return "UNT Merch"
    if "carhartt" in u: return "Outerwear"
    if "macys" in u: return "Shirts"
    if "menswearhouse" in u: return "Menswear"
    if "pacsun" in u: return "Graphic Tee"
    return "Misc"


# Strong browser-spoof headers (fixes Access Denied at North Face, Amazon)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
}


# Try OpenGraph, Twitter Card, or first <img> fallback
def scrape_image(soup):
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og["content"]

    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        return tw["content"]

    for img in soup.find_all("img"):
        src = img.get("src") or ""
        if src.startswith("http"):
            return src

    return ""


# =============================
# Main Scraper
# =============================
def scrape_item(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # ----- SPECIAL CASE: NIKE (custom + regular) -----
        if "nike.com" in url.lower():
            try:
                script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
                if script_tag:
                    data_json = json.loads(script_tag.text)

                    product = (
                        data_json.get("props", {})
                                .get("pageProps", {})
                                .get("product")
                        or {}
                    )

                    title = (
                        product.get("title")
                        or product.get("subtitle")
                        or "Nike Item"
                    )
                    title = clean_title(title)

                    # Try multiple possible image keys
                    images = product.get("images", [])
                    image_url = ""

                    if images:
                        img0 = images[0]
                        for key in [
                            "portraitURL", "squarishURL",
                            "fullSizeURL", "url", "imageUrl"
                        ]:
                            if key in img0 and img0[key]:
                                image_url = img0[key]
                                break

                    return title, image_url, "Shoes"

            except:
                pass  # fallback to default below

        # ----- DEFAULT SCRAPER -----
        raw_title = soup.find("title").text if soup.find("title") else "Unknown Item"
        title = clean_title(raw_title)

        img = scrape_image(soup)
        cat = detect_category(url, title)

        return title, img, cat

    except:
        return "Unknown Item", "", "Misc"


# =============================
# Streamlit Setup
# =============================
st.set_page_config(page_title="Sam's Wishlist", layout="wide")
data = load_data()

# Dark mode
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>
        body, .stApp { background-color:#1a1a1a !important; color:white !important; }
        .stButton button { background-color:#333 !important; color:white !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

st.title("🎁 Sam’s 2025 Wishlist")


# =============================
# Preferences Section
# =============================
st.header("Your Preferences")

shirt_size = st.text_input("Shirt size:", data["preferences"].get("shirt_size", ""))
jacket_size = st.text_input("Jacket size:", data["preferences"].get("jacket_size", ""))
pants_size = st.text_input("Pants size:", data["preferences"].get("pants_size", ""))
shoe_size = st.text_input("Shoe size:", data["preferences"].get("shoe_size", ""))
styles = st.text_input("Preferred colors/styles:", data["preferences"].get("styles", ""))

if st.button("Save Preferences"):
    data["preferences"]["shirt_size"] = shirt_size
    data["preferences"]["jacket_size"] = jacket_size
    data["preferences"]["pants_size"] = pants_size
    data["preferences"]["shoe_size"] = shoe_size
    data["preferences"]["styles"] = styles
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

    item = {
        "name": title,
        "url": new_url,
        "image": img,
        "category": auto_cat,
        "priority": priority,
        "purchased": False,
    }

    data["items"].append(item)
    save_data(data)
    st.success("Item added!")
    st.rerun()


# =============================
# Filters
# =============================
st.header("Your Wishlist")

all_categories = sorted(list({i["category"] for i in data["items"]}))
filter_cat = st.multiselect("Filter by category:", all_categories)
filter_priority = st.multiselect("Filter by priority:", ["High", "Medium", "Low"])
search = st.text_input("Search items:")

filtered = data["items"]

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
        with st.container():

            if item["image"]:
                st.image(item["image"], width=260)
            else:
                st.write("(no image)")

            st.subheader(item["name"])
            st.write(f"**Category:** {item['category']}")
            st.write(f"**Priority:** {item['priority']}")
            st.write(f"[View Item]({item['url']})")

            purchased_flag = st.checkbox(
                "Purchased?",
                value=item.get("purchased", False),
                key=f"p_{idx}"
            )

            if purchased_flag != item.get("purchased", False):
                item["purchased"] = purchased_flag
                save_data(data)

            if st.button("❌ Remove", key=f"rm_{idx}"):
                data["items"].remove(item)
                save_data(data)
                st.warning("Removed.")
                st.rerun()
print("APP LOADED")
