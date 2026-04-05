"""Bones API — a database of human bone images and metadata."""

import os
import random

from flask import Flask, jsonify, send_from_directory

from bones.catalog import BONES, BONES_BY_ID, REGIONS

app = Flask(__name__)

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")


def _find_image(bone_id):
    """Find the image file for a bone, regardless of extension."""
    for ext in ("png", "jpg", "svg"):
        path = os.path.join(IMAGES_DIR, f"{bone_id}.{ext}")
        if os.path.exists(path):
            return f"{bone_id}.{ext}"
    return None


def _bone_to_dict(bone):
    """Convert a bone catalog entry to an API response dict."""
    image_file = _find_image(bone["id"])
    return {
        "id": bone["id"],
        "name": bone["name"],
        "region": bone["region"],
        "sub_region": bone["sub_region"],
        "description": bone["description"],
        "image": f"/images/{image_file}" if image_file else None,
        "has_image": image_file is not None,
    }


@app.route("/")
def index():
    return jsonify(
        {
            "name": "Bones API",
            "description": "A database of human bone images and metadata",
            "total_bones": len(BONES),
            "endpoints": {
                "/bones": "List all bones",
                "/bones/<id>": "Get a specific bone",
                "/bones/random": "Get a random bone",
                "/bones/region/<region>": "List bones by region",
                "/regions": "List all regions",
                "/images/<filename>": "Get a bone image",
            },
        }
    )


@app.route("/bones")
def list_bones():
    region = None
    # Support ?region= filter
    from flask import request

    region = request.args.get("region")
    bones = BONES
    if region:
        bones = [b for b in bones if b["region"] == region]
    return jsonify([_bone_to_dict(b) for b in bones])


@app.route("/bones/random")
def random_bone():
    from flask import request

    region = request.args.get("region")
    bones = BONES
    if region:
        bones = [b for b in bones if b["region"] == region]

    only_with_images = request.args.get("has_image", "").lower() == "true"
    if only_with_images:
        bones = [b for b in bones if _find_image(b["id"])]

    if not bones:
        return jsonify({"error": "No bones found"}), 404
    return jsonify(_bone_to_dict(random.choice(bones)))


@app.route("/bones/<bone_id>")
def get_bone(bone_id):
    bone = BONES_BY_ID.get(bone_id)
    if not bone:
        return jsonify({"error": "Bone not found"}), 404
    return jsonify(_bone_to_dict(bone))


@app.route("/regions")
def list_regions():
    return jsonify(REGIONS)


@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)
