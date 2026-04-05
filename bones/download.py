"""Download bone images from eSkeletons.org and Wikimedia Commons."""

import os
import time

import requests

from bones.catalog import BONES

HEADERS = {"User-Agent": "Bones/1.0 (anatomy image database)"}
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")

# eSkeletons.org URL mapping: bone_id -> (region, bone_name, preferred_orientation)
ESKELETONS = {
    # Skull — cranial
    "frontal": ("skull", "frontal", "Superior"),
    "parietal": ("skull", "parietal", "Lateral"),
    "temporal": ("skull", "temporal", "Lateral"),
    "occipital": ("skull", "occipital", "Posterior"),
    "sphenoid": ("skull", "sphenoid", "Anterior"),
    "ethmoid": ("skull", "ethmoid", "Anterior"),
    # Skull — facial
    "mandible": ("skull", "mandible", "Lateral"),
    "maxilla": ("skull", "maxilla", "Anterior"),
    "zygomatic": ("skull", "zygomatic", "Lateral"),
    "nasal": ("skull", "nasal", "Anterior"),
    "lacrimal": ("skull", "lacrimal", "Lateral"),
    # Throat
    "hyoid": ("skull", "hyoid", "Anterior"),
    # Thorax
    "sternum": ("thorax", "sternum", "Anterior"),
    "rib": ("thorax", "rib_7", "Anterior"),
    # Shoulder / upper limb
    "clavicle": ("upper_limb", "clavicle", "Anterior"),
    "scapula": ("upper_limb", "scapula", "Anterior"),
    "humerus": ("upper_limb", "humerus", "Anterior"),
    "radius": ("upper_limb", "radius", "Anterior"),
    "ulna": ("upper_limb", "ulna", "Anterior"),
    # Wrist (carpals)
    "scaphoid": ("hands", "scaphoid", "Dorsal"),
    "lunate": ("hands", "lunate", "Dorsal"),
    "triquetral": ("hands", "triquetral", "Dorsal"),
    "pisiform": ("hands", "pisiform", "Dorsal"),
    "trapezium": ("hands", "trapezium", "Dorsal"),
    "trapezoid": ("hands", "trapezoid", "Dorsal"),
    "capitate": ("hands", "capitate", "Dorsal"),
    "hamate": ("hands", "hamate", "Dorsal"),
    # Hand
    "metacarpals": ("hands", "metacarpal_3", "Dorsal"),
    "proximal-phalanx-hand": ("hands", "manual_proximal_phalanx_3", "Dorsal"),
    # Pelvis
    "hip-bone": ("lower_limb", "os_coxa", "Anterior"),
    "ilium": ("lower_limb", "os_coxa", "Lateral"),
    "ischium": ("lower_limb", "os_coxa", "Medial"),
    "pubis": ("lower_limb", "os_coxa", "Anterior"),
    # Lower limb
    "femur": ("lower_limb", "femur", "Anterior"),
    "patella": ("lower_limb", "patella", "Anterior"),
    "tibia": ("lower_limb", "tibia", "Anterior"),
    "fibula": ("lower_limb", "fibula", "Anterior"),
    # Ankle (tarsals)
    "calcaneus": ("feet", "calcaneus", "Dorsal"),
    "talus": ("feet", "talus", "Dorsal"),
    "navicular": ("feet", "navicular", "Dorsal"),
    "cuboid": ("feet", "cuboid", "Dorsal"),
    "medial-cuneiform": ("feet", "medial_cuneiform", "Dorsal"),
    "intermediate-cuneiform": ("feet", "intermediate_cuneiform", "Dorsal"),
    "lateral-cuneiform": ("feet", "lateral_cuneiform", "Dorsal"),
    # Foot
    "metatarsals": ("feet", "metatarsal_3", "Dorsal"),
    "proximal-phalanx-foot": ("feet", "pedal_proximal_phalanx_1", "Dorsal"),
}


def get_eskeletons_image(bone_id):
    """Get an image URL from eSkeletons.org."""
    mapping = ESKELETONS.get(bone_id)
    if not mapping:
        return None
    region, bone_name, orientation = mapping
    return (
        f"https://www.eskeletons.org/files/image/orientation/"
        f"human_{region}_{bone_name}_{orientation}.jpg"
    )


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
    good_files = []

    for page in pages.values():
        for img in page.get("images", []):
            fname = img["title"].lower()
            if "commons-logo" in fname or "icon" in fname:
                continue
            is_grays = "gray" in fname
            has_name = any(kw in fname for kw in keywords)
            if is_grays or has_name:
                good_files.append((img["title"], is_grays))

    if not good_files:
        return None

    good_files.sort(key=lambda x: (not x[1], x[0]))
    chosen = good_files[0][0]

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
            return info.get("thumburl") or info.get("url")
    return None


def download_image(url, filepath):
    """Download an image to disk."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        content_type = resp.headers.get("content-type", "")
        is_image = content_type.startswith("image/")
        if resp.status_code == 200 and is_image and len(resp.content) > 500:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False


def download_all(force=False):
    """Download images for all bones in the catalog.

    Uses eSkeletons.org as the primary source (clean photos),
    with Wikimedia Commons as fallback.

    Pass force=True to re-download all images.
    """
    os.makedirs(IMAGES_DIR, exist_ok=True)

    found = 0
    missing = []

    for bone in BONES:
        bone_id = bone["id"]

        if not force:
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

        # Try eSkeletons first (consistent, clean photos)
        sources = [
            ("eskeletons", get_eskeletons_image(bone_id)),
            ("grays", get_grays_image(name)),
            ("wikipedia", get_wikipedia_article_images(name)),
            ("wikipedia", get_wikipedia_image(name)),
        ]

        downloaded = False
        for source_name, url in sources:
            if not url:
                continue
            ext = "png" if ".png" in url.lower() else "jpg"
            if ".svg" in url.lower():
                ext = "svg"
            filepath = os.path.join(IMAGES_DIR, f"{bone_id}.{ext}")
            if download_image(url, filepath):
                print(f"ok ({source_name})")
                found += 1
                downloaded = True
                break

        if not downloaded:
            print("not found")
            missing.append(bone["name"])

        time.sleep(0.3)

    print(f"\nDone: {found}/{len(BONES)} images downloaded")
    if missing:
        print(f"Missing: {', '.join(missing)}")


if __name__ == "__main__":
    import sys

    force = "--force" in sys.argv
    download_all(force=force)
