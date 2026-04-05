"""Download bone images from Wikimedia Commons (Gray's Anatomy illustrations)."""

import hashlib
import os
import time

import requests

from bones.catalog import BONES

HEADERS = {"User-Agent": "Bones/1.0 (anatomy image database)"}
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")


def get_grays_image(search_term):
    """Search Wikimedia Commons for a Gray's Anatomy illustration."""
    resp = requests.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srnamespace": 6,
            "srsearch": f"Gray's Anatomy {search_term}",
            "srlimit": 10,
            "format": "json",
        },
        headers=HEADERS,
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    results = resp.json().get("query", {}).get("search", [])
    if not results:
        return None

    # Prefer results with the bone name in the title
    name_lower = search_term.lower().split("(")[0].strip()
    chosen = results[0]["title"]
    for r in results:
        title_lower = r["title"].lower()
        if any(word in title_lower for word in name_lower.split() if len(word) > 3):
            chosen = r["title"]
            break

    return get_file_url(chosen)


def get_wikipedia_image(title):
    """Fetch the main image from a Wikipedia article."""
    resp = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "titles": title,
            "prop": "pageimages",
            "pithumbsize": 800,
            "format": "json",
        },
        headers=HEADERS,
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    pages = resp.json().get("query", {}).get("pages", {})
    for page in pages.values():
        thumb = page.get("thumbnail", {}).get("source")
        if thumb:
            return thumb
    return None


def get_wikipedia_article_images(title):
    """Search all images on a Wikipedia article for anatomical illustrations."""
    resp = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "titles": title,
            "prop": "images",
            "imlimit": 50,
            "format": "json",
        },
        headers=HEADERS,
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    pages = resp.json().get("query", {}).get("pages", {})

    name_lower = title.split("(")[0].strip().lower()
    keywords = [w for w in name_lower.split() if len(w) > 3]
    # Also look for Gray's or anatomical terms
    good_files = []

    for page in pages.values():
        for img in page.get("images", []):
            fname = img["title"].lower()
            if "commons-logo" in fname or "icon" in fname:
                continue
            # Prefer Gray's illustrations or files with the bone name
            is_grays = "gray" in fname
            has_name = any(kw in fname for kw in keywords)
            if is_grays or has_name:
                good_files.append((img["title"], is_grays))

    if not good_files:
        return None

    # Prefer Gray's illustrations
    good_files.sort(key=lambda x: (not x[1], x[0]))
    chosen = good_files[0][0]

    # Get image URL via the Wikipedia imageinfo API
    resp2 = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "titles": chosen,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 800,
            "format": "json",
        },
        headers=HEADERS,
        timeout=10,
    )
    if resp2.status_code != 200:
        return None
    pages2 = resp2.json().get("query", {}).get("pages", {})
    for page in pages2.values():
        if "imageinfo" in page:
            info = page["imageinfo"][0]
            return info.get("thumburl") or info.get("url")
    return None


def get_file_url(file_title):
    """Get the actual image URL for a Wikimedia Commons file."""
    resp = requests.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 800,
            "format": "json",
        },
        headers=HEADERS,
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    pages = resp.json().get("query", {}).get("pages", {})
    for page in pages.values():
        if "imageinfo" in page:
            info = page["imageinfo"][0]
            # Prefer thumburl, fall back to full url
            return info.get("thumburl") or info.get("url")
    return None


def download_image(url, filepath):
    """Download an image to disk."""
    resp = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    if resp.status_code == 200 and len(resp.content) > 500:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return True
    return False


def download_all():
    """Download images for all bones in the catalog."""
    os.makedirs(IMAGES_DIR, exist_ok=True)

    found = 0
    missing = []

    for bone in BONES:
        bone_id = bone["id"]
        # Check if already downloaded (any extension)
        existing = [
            f
            for f in os.listdir(IMAGES_DIR)
            if f.startswith(bone_id + ".") and not f.endswith(".json")
        ]
        if existing:
            print(f"  skip {bone['name']} (already have {existing[0]})")
            found += 1
            continue

        name = bone["wikipedia"]
        print(f"  fetch {bone['name']}...", end=" ", flush=True)

        sources = [
            get_grays_image(name),
            get_wikipedia_article_images(name),
            get_wikipedia_image(name),
        ]

        downloaded = False
        for url in sources:
            if not url:
                continue
            ext = "png" if ".png" in url.lower() else "jpg"
            if ".svg" in url.lower():
                ext = "svg"
            filepath = os.path.join(IMAGES_DIR, f"{bone_id}.{ext}")
            if download_image(url, filepath):
                print(f"ok ({ext})")
                found += 1
                downloaded = True
                break

        if not downloaded:
            print("not found")
            missing.append(bone["name"])

        time.sleep(0.5)  # be polite to the API

    print(f"\nDone: {found}/{len(BONES)} images downloaded")
    if missing:
        print(f"Missing: {', '.join(missing)}")


if __name__ == "__main__":
    download_all()
