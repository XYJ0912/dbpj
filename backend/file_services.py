import hashlib
import os
import re
from pathlib import Path


LOCAL_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
]


def path_exists(path):
    if not path:
        return False
    return Path(path).exists()


def file_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def sha256_file(path, chunk_size=1024 * 1024):
    if not path_exists(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contains_local_path(value):
    text = str(value or "")
    return any(pattern.search(text) for pattern in LOCAL_PATH_PATTERNS)


def public_asset_url(row):
    if row.get("public_export_path"):
        return row["public_export_path"]
    if row.get("thumbnail_path"):
        return row["thumbnail_path"]
    media_id = row.get("media_id", "asset")
    return f"assets/media/{media_id}"
