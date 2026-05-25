import os
import re
import uuid
from html import escape
from pathlib import Path

from flask import Blueprint, Response, abort, g, request, send_file
from werkzeug.utils import secure_filename

from auth import login_required
from config import Config
from db import execute, query, query_one
from document_extract import extract_asset_text
from response import error, success


bp = Blueprint("assets", __name__, url_prefix="/api/assets")
UPLOAD_ROOT = Path(Config.UPLOAD_ROOT).resolve() if Config.UPLOAD_ROOT else Path(__file__).resolve().parents[2] / "uploads"


def clean_path(value):
    return (value or "").strip().strip('"').strip("'")


def asset_name_from_payload(payload):
    name = (payload.get("asset_name") or "").strip()
    if name:
        return name
    path = clean_path(payload.get("local_path")) or clean_path(payload.get("public_export_path")) or "untitled-asset"
    return Path(path).name or "untitled-asset"


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".avif"}
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".mkv", ".avi"}
AUDIO_SUFFIXES = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}
DOCUMENT_SUFFIXES = {".pdf", ".txt", ".md", ".markdown", ".doc", ".docx", ".ppt", ".pptx"}


def media_type_from_mime(mime_type, filename=""):
    suffix = Path(filename or "").suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    if suffix in DOCUMENT_SUFFIXES:
        return "document"
    if not mime_type:
        return "other"
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("video/"):
        return "video"
    if mime_type.startswith("audio/"):
        return "audio"
    if mime_type in {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        return "document"
    return "other"


def suffix_from_asset(asset, candidate=None):
    for value in (asset.get("asset_name"), candidate, asset.get("local_path"), asset.get("public_export_path"), asset.get("thumbnail_path")):
        suffix = Path(str(value or "")).suffix.lower()
        if suffix:
            return suffix
    mime = asset.get("mime_type") or ""
    if mime == "text/markdown":
        return ".md"
    if mime == "text/plain":
        return ".txt"
    if mime == "application/pdf":
        return ".pdf"
    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return ".docx"
    if mime == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        return ".pptx"
    return ""


def get_asset(asset_id):
    return query_one(
        "SELECT * FROM v_workspace_asset WHERE owner_id = %s AND asset_id = %s",
        (g.user_id, asset_id),
    )


def render_inline_markdown(text):
    value = escape(str(text or ""))
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    return value


def render_markdown_preview(text, title):
    lines = str(text or "").splitlines()
    html = []
    paragraph = []
    list_open = False
    code_open = False
    code_lines = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            html.append(f"<p>{render_inline_markdown(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list():
        nonlocal list_open
        if list_open:
            html.append("</ul>")
            list_open = False

    for raw in lines:
        line = raw.rstrip()
        if line.strip().startswith("```"):
            flush_paragraph()
            close_list()
            if code_open:
                html.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                code_open = False
            else:
                code_open = True
            continue
        if code_open:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            close_list()
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            html.append(f"<h{level}>{render_inline_markdown(heading.group(2))}</h{level}>")
            continue
        item = re.match(r"^[-*]\s+(.+)$", line)
        if item:
            flush_paragraph()
            if not list_open:
                html.append("<ul>")
                list_open = True
            html.append(f"<li>{render_inline_markdown(item.group(1))}</li>")
            continue
        quote = re.match(r"^>\s?(.+)$", line)
        if quote:
            flush_paragraph()
            close_list()
            html.append(f"<blockquote>{render_inline_markdown(quote.group(1))}</blockquote>")
            continue
        paragraph.append(line.strip())

    if code_open:
        html.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
    flush_paragraph()
    close_list()
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title or "Markdown preview")}</title>
  <style>
    body {{ margin: 0; padding: 24px; color: #231f1b; background: #fbf7ef; font: 16px/1.75 Georgia, 'Times New Roman', 'Microsoft YaHei', sans-serif; }}
    main {{ max-width: 860px; margin: 0 auto; }}
    h1, h2, h3, h4 {{ margin: 1.2em 0 .45em; line-height: 1.2; }}
    h1 {{ font-size: 34px; }}
    h2 {{ font-size: 26px; }}
    h3 {{ font-size: 21px; }}
    p {{ margin: 0 0 1em; }}
    ul {{ padding-left: 1.4em; }}
    blockquote {{ margin: 1em 0; padding-left: 1em; border-left: 3px solid #8fb8a8; color: #5f665f; }}
    pre {{ overflow: auto; padding: 14px; border-radius: 8px; background: #f0ebe2; }}
    code {{ font-family: Consolas, 'Courier New', monospace; font-size: .94em; }}
  </style>
</head>
<body><main>{''.join(html) or '<p>No preview text.</p>'}</main></body>
</html>"""


@bp.get("")
@login_required
def index():
    clauses = ["owner_id = %s"]
    params = [g.user_id]
    if request.args.get("status") == "archived":
        clauses.append("import_status = 'archived'")
    elif request.args.get("include_archived") != "true":
        clauses.append("import_status <> 'archived'")
    if request.args.get("visibility"):
        clauses.append("visibility = %s")
        params.append(request.args["visibility"])
    rows = query(
        "SELECT * FROM v_workspace_asset WHERE "
        + " AND ".join(clauses)
        + " ORDER BY created_at DESC, asset_id DESC",
        params,
    )
    return success(rows)


@bp.post("/import")
@login_required
def import_reference():
    payload = request.get_json(silent=True) or {}
    local_path = clean_path(payload.get("local_path"))
    public_export_path = clean_path(payload.get("public_export_path"))
    thumbnail_path = clean_path(payload.get("thumbnail_path"))
    exists = bool(local_path and os.path.exists(local_path))
    file_size = os.path.getsize(local_path) if exists else payload.get("file_size")

    execute(
        """INSERT INTO media_asset
           (owner_id, asset_name, media_type, local_path, thumbnail_path, public_export_path,
            file_size, mime_type, visibility, import_status, file_exists, last_checked_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
        (
            g.user_id,
            asset_name_from_payload(payload),
            payload.get("media_type") or media_type_from_mime(payload.get("mime_type"), local_path or public_export_path),
            local_path or None,
            thumbnail_path or None,
            public_export_path or None,
            file_size,
            payload.get("mime_type"),
            payload.get("visibility") or "public",
            payload.get("import_status") or "active",
            exists,
        ),
    )
    asset_id = query_one("SELECT LAST_INSERT_ID() AS id")["id"]
    upsert_license(asset_id, payload)
    return success(get_asset(asset_id), msg="asset imported")


@bp.post("/upload")
@login_required
def upload():
    files = request.files.getlist("files")
    if not files:
        return error("no files uploaded")

    visibility = request.form.get("visibility") or "public"
    upload_dir = UPLOAD_ROOT / f"user-{g.user_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    created = []

    for item in files:
        if not item or not item.filename:
            continue
        original_name = Path(item.filename).name
        safe_name = secure_filename(original_name) or "asset"
        original_suffix = Path(original_name).suffix.lower()
        if original_suffix and not Path(safe_name).suffix:
            safe_name = f"{safe_name}{original_suffix}"
        stored_name = f"{uuid.uuid4().hex}-{safe_name}"
        target = upload_dir / stored_name
        item.save(target)
        mime_type = item.mimetype or None
        media_type = media_type_from_mime(mime_type, original_name)

        execute(
            """INSERT INTO media_asset
               (owner_id, asset_name, media_type, local_path, public_export_path,
                file_size, mime_type, visibility, import_status, file_exists, last_checked_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', TRUE, NOW())""",
            (
                g.user_id,
                original_name,
                media_type,
                str(target),
                None,
                os.path.getsize(target),
                mime_type,
                visibility,
            ),
        )
        asset_id = query_one("SELECT LAST_INSERT_ID() AS id")["id"]
        upsert_license(
            asset_id,
            {
                "authorization_status": request.form.get("authorization_status") or "licensed",
                "allow_public_display": request.form.get("allow_public_display") == "true",
            },
        )
        created.append(get_asset(asset_id))

    return success(created, msg=f"{len(created)} asset(s) uploaded")


@bp.get("/<int:asset_id>/preview")
def preview(asset_id):
    asset = query_one(
        "SELECT asset_id, asset_name, media_type, local_path, thumbnail_path, public_export_path, mime_type FROM media_asset WHERE asset_id = %s",
        (asset_id,),
    )
    if not asset or asset["media_type"] not in ("image", "video", "audio", "document", "other"):
        abort(404)
    fields = ("thumbnail_path", "public_export_path", "local_path") if asset["media_type"] == "image" else ("public_export_path", "local_path")
    for field in fields:
        candidate = clean_path(asset.get(field))
        if candidate and os.path.exists(candidate):
            suffix = suffix_from_asset(asset, candidate)
            if suffix in {".md", ".markdown"}:
                text, _reason = extract_asset_text(candidate, asset.get("mime_type"), asset.get("asset_name"))
                return Response(
                    render_markdown_preview(text, asset.get("asset_name") or Path(candidate).name),
                    mimetype="text/html",
                    headers={"Content-Disposition": "inline"},
                )
            return send_file(candidate, mimetype=asset.get("mime_type") or None, conditional=True)
    abort(404)


@bp.get("/<int:asset_id>/text")
@login_required
def text_preview(asset_id):
    asset = get_asset(asset_id)
    if not asset:
        return error("asset not found", http_status=404)
    for field in ("local_path", "public_export_path"):
        candidate = clean_path(asset.get(field))
        if candidate and os.path.exists(candidate):
            text, reason = extract_asset_text(candidate, asset.get("mime_type"), asset.get("asset_name"))
            return success({"text": text, "warning": reason})
    return error("asset source file not found", http_status=404)


@bp.patch("/<int:asset_id>")
@login_required
def update(asset_id):
    if not get_asset(asset_id):
        return error("asset not found", http_status=404)
    payload = request.get_json(silent=True) or {}
    allowed = {
        "asset_name",
        "media_type",
        "thumbnail_path",
        "public_export_path",
        "mime_type",
        "visibility",
        "import_status",
    }
    assignments = []
    params = []
    for field in allowed:
        if field in payload:
            assignments.append(f"{field} = %s")
            params.append(payload[field])
    if assignments:
        params.extend([asset_id, g.user_id])
        execute(
            f"UPDATE media_asset SET {', '.join(assignments)} WHERE asset_id = %s AND owner_id = %s",
            params,
        )
    upsert_license(asset_id, payload)
    return success(get_asset(asset_id), msg="asset updated")


@bp.post("/<int:asset_id>/archive")
@login_required
def archive(asset_id):
    affected = execute(
        "UPDATE media_asset SET import_status = 'archived' WHERE asset_id = %s AND owner_id = %s",
        (asset_id, g.user_id),
    )
    if not affected:
        return error("asset not found", http_status=404)
    return success(msg="asset archived")


@bp.post("/<int:asset_id>/restore")
@login_required
def restore(asset_id):
    affected = execute(
        "UPDATE media_asset SET import_status = 'active' WHERE asset_id = %s AND owner_id = %s",
        (asset_id, g.user_id),
    )
    if not affected:
        return error("asset not found", http_status=404)
    return success(get_asset(asset_id), msg="asset restored")


@bp.delete("/<int:asset_id>")
@login_required
def delete(asset_id):
    asset = get_asset(asset_id)
    if not asset:
        return error("asset not found", http_status=404)
    execute("DELETE FROM work_media WHERE asset_id = %s", (asset_id,))
    execute("DELETE FROM asset_license_note WHERE asset_id = %s", (asset_id,))
    affected = execute(
        "DELETE FROM media_asset WHERE asset_id = %s AND owner_id = %s",
        (asset_id, g.user_id),
    )
    if not affected:
        return error("asset not found", http_status=404)
    return success(msg="asset deleted")


def upsert_license(asset_id, payload):
    fields = {
        "authorization_status",
        "source_name",
        "source_url",
        "license_note",
        "allow_public_display",
        "attribution_required",
    }
    if not any(field in payload for field in fields):
        return
    execute(
        """INSERT INTO asset_license_note
           (asset_id, authorization_status, source_name, source_url, license_note,
            allow_public_display, attribution_required)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE
             authorization_status = VALUES(authorization_status),
             source_name = VALUES(source_name),
             source_url = VALUES(source_url),
             license_note = VALUES(license_note),
             allow_public_display = VALUES(allow_public_display),
             attribution_required = VALUES(attribution_required)""",
        (
            asset_id,
            payload.get("authorization_status") or "unknown",
            payload.get("source_name"),
            payload.get("source_url"),
            payload.get("license_note"),
            bool(payload.get("allow_public_display")),
            bool(payload.get("attribution_required")),
        ),
    )
