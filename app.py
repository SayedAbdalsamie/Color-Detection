"""
Color Detection — Flask web application.
Click-to-identify colors + KMeans dominant palette (computed once per upload).
"""

from __future__ import annotations

import os
import re
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request
from sklearn.cluster import KMeans
from werkzeug.utils import secure_filename

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "bmp"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_IMAGE_WIDTH = 1600
MAX_IMAGE_HEIGHT = 1200
KMEANS_SAMPLE = 12000
CACHE_TTL_SECONDS = 3600
MAX_CACHE_ENTRIES = 50

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# upload_id -> { path, width, height, dominant, created }
_upload_cache: dict[str, dict] = {}


def _cleanup_cache() -> None:
    now = time.time()
    expired = [k for k, v in _upload_cache.items() if now - v["created"] > CACHE_TTL_SECONDS]
    for k in expired:
        p = _upload_cache.pop(k, None)
        if p and p.get("path"):
            try:
                Path(p["path"]).unlink(missing_ok=True)
            except OSError:
                pass
    while len(_upload_cache) > MAX_CACHE_ENTRIES:
        oldest = min(_upload_cache.items(), key=lambda x: x[1]["created"])[0]
        p = _upload_cache.pop(oldest, None)
        if p and p.get("path"):
            try:
                Path(p["path"]).unlink(missing_ok=True)
            except OSError:
                pass


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Load color dataset once
def _load_colors_df() -> pd.DataFrame:
    csv_path = BASE_DIR / "colors.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"colors.csv not found at {csv_path}")
    df = pd.read_csv(csv_path, header=None)
    df.columns = ["id", "color_name", "hex", "r", "g", "b"]
    return df


_COLORS_DF: pd.DataFrame | None = None
_RGB_ARRAY: np.ndarray | None = None


def _ensure_colors() -> None:
    global _COLORS_DF, _RGB_ARRAY
    if _COLORS_DF is None:
        _COLORS_DF = _load_colors_df()
        _RGB_ARRAY = _COLORS_DF[["r", "g", "b"]].to_numpy(dtype=np.int32)


def get_color_name(r: int, g: int, b: int) -> str:
    _ensure_colors()
    assert _RGB_ARRAY is not None and _COLORS_DF is not None
    target = np.array([[r, g, b]], dtype=np.int32)
    dist = np.abs(_RGB_ARRAY - target).sum(axis=1)
    idx = int(np.argmin(dist))
    return str(_COLORS_DF.iloc[idx]["color_name"])


def resize_image(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    scale = min(MAX_IMAGE_WIDTH / w, MAX_IMAGE_HEIGHT / h, 1.0)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def dominant_colors_kmeans(img_bgr: np.ndarray, k: int = 5) -> list[dict]:
    """BGR image -> top k colors by cluster size, RGB + name."""
    pixels = img_bgr.reshape(-1, 3).astype(np.float32)
    n = len(pixels)
    if n == 0:
        return []
    k = min(k, max(1, n))
    sample_n = min(KMEANS_SAMPLE, n)
    if sample_n < n:
        idx = np.random.choice(n, sample_n, replace=False)
        sample = pixels[idx]
    else:
        sample = pixels

    n_init = min(10, max(3, sample_n // 2000))
    kmeans = KMeans(n_clusters=k, n_init=n_init, random_state=42, max_iter=300)
    kmeans.fit(sample)
    centers = kmeans.cluster_centers_.astype(np.int32)
    labels = kmeans.labels_
    counts = np.bincount(labels, minlength=k)
    order = np.argsort(counts)[::-1]

    out = []
    for i in order[:k]:
        b, g, r = int(centers[i, 0]), int(centers[i, 1]), int(centers[i, 2])
        r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
        name = get_color_name(r, g, b)
        out.append(
            {
                "r": r,
                "g": g,
                "b": b,
                "name": name,
                "hex": f"#{r:02x}{g:02x}{b:02x}",
            }
        )
    return out


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/upload")
def api_upload():
    _cleanup_cache()
    if "image" not in request.files:
        return jsonify({"ok": False, "error": "No file field 'image'."}), 400
    f = request.files["image"]
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "No file selected."}), 400
    if not _allowed_file(f.filename):
        return jsonify(
            {"ok": False, "error": f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."}
        ), 400

    ext = secure_filename(f.filename).rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"ok": False, "error": "Invalid extension."}), 400

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    upload_id = str(uuid.uuid4())
    safe_name = f"{upload_id}.{ext}"
    path = UPLOAD_DIR / safe_name

    try:
        f.save(str(path))
    except OSError as e:
        return jsonify({"ok": False, "error": f"Could not save file: {e}"}), 500

    img = cv2.imread(str(path))
    if img is None:
        path.unlink(missing_ok=True)
        return jsonify({"ok": False, "error": "Could not read image. Corrupt or unsupported format."}), 400

    img = resize_image(img)
    cv2.imwrite(str(path), img)
    h, w = img.shape[:2]

    try:
        dominant = dominant_colors_kmeans(img, k=5)
    except Exception as e:
        path.unlink(missing_ok=True)
        return jsonify({"ok": False, "error": f"Palette analysis failed: {e}"}), 500

    url_path = f"/static/uploads/{safe_name}"
    _upload_cache[upload_id] = {
        "path": str(path),
        "width": w,
        "height": h,
        "dominant": dominant,
        "created": time.time(),
    }

    return jsonify(
        {
            "ok": True,
            "upload_id": upload_id,
            "image_url": url_path,
            "width": w,
            "height": h,
            "dominant_colors": dominant,
        }
    )


@app.post("/api/pixel")
def api_pixel():
    data = request.get_json(silent=True) or {}
    upload_id = data.get("upload_id")
    try:
        x = int(data.get("x"))
        y = int(data.get("y"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid coordinates."}), 400

    if not upload_id or not isinstance(upload_id, str):
        return jsonify({"ok": False, "error": "Missing upload_id."}), 400
    if not re.match(r"^[a-f0-9-]{36}$", upload_id, re.I):
        return jsonify({"ok": False, "error": "Invalid upload_id."}), 400

    entry = _upload_cache.get(upload_id)
    if not entry:
        return jsonify({"ok": False, "error": "Upload expired or not found. Please upload again."}), 404

    w, h = entry["width"], entry["height"]
    if x < 0 or y < 0 or x >= w or y >= h:
        return jsonify({"ok": False, "error": f"Coordinates out of bounds (0–{w - 1}, 0–{h - 1})."}), 400

    img = cv2.imread(entry["path"])
    if img is None:
        return jsonify({"ok": False, "error": "Image file missing on server."}), 500

    b, g, r = [int(v) for v in img[y, x]]
    name = get_color_name(r, g, b)

    return jsonify(
        {
            "ok": True,
            "r": r,
            "g": g,
            "b": b,
            "name": name,
            "hex": f"#{r:02x}{g:02x}{b:02x}",
        }
    )


@app.get("/api/dominant/<upload_id>")
def api_dominant(upload_id: str):
    if not re.match(r"^[a-f0-9-]{36}$", upload_id, re.I):
        return jsonify({"ok": False, "error": "Invalid upload_id."}), 400
    entry = _upload_cache.get(upload_id)
    if not entry:
        return jsonify({"ok": False, "error": "Upload not found."}), 404
    return jsonify({"ok": True, "dominant_colors": entry["dominant"]})


@app.errorhandler(413)
def too_large(_e):
    return jsonify({"ok": False, "error": "File too large (max 15 MB)."}), 413


try:
    _ensure_colors()
except FileNotFoundError:
    pass  # Fail on first request with clear error if CSV missing


if __name__ == "__main__":
    _ensure_colors()
    app.run(debug=True, host="0.0.0.0", port=5000)
