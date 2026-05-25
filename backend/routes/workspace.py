from flask import Blueprint, g, request

from auth import login_required
from db import execute, query, query_one
from document_extract import extract_asset_text, summarize_text
from response import error, success


bp = Blueprint("workspace", __name__, url_prefix="/api/workspace")


def get_work(work_id):
    work = query_one(
        """SELECT w.*,
                  (SELECT COUNT(*) FROM work_media wm WHERE wm.work_id = w.work_id) AS asset_count,
                  (SELECT COUNT(*) FROM work_media wm WHERE wm.work_id = w.work_id AND wm.is_public) AS public_asset_count
             FROM work w
            WHERE w.owner_id = %s AND w.work_id = %s""",
        (g.user_id, work_id),
    )
    if not work:
        return None
    work["assets"] = query(
        """SELECT wm.work_id, wm.asset_id, wm.role, wm.display_order, wm.is_public, a.*
             FROM work_media wm
             JOIN v_workspace_asset a ON a.asset_id = wm.asset_id
            WHERE wm.work_id = %s
            ORDER BY wm.display_order, wm.asset_id""",
        (work_id,),
    )
    work["tags"] = query(
        """SELECT t.tag_id, t.tag_name, t.tag_type
             FROM work_tag wt
             JOIN tag t ON t.tag_id = wt.tag_id
            WHERE wt.work_id = %s AND t.tag_status = 'active'
            ORDER BY t.tag_type, t.tag_name""",
        (work_id,),
    )
    return work


@bp.get("/overview")
@login_required
def overview():
    row = query_one(
        """SELECT
             (SELECT COUNT(*) FROM media_asset WHERE owner_id = %s AND import_status <> 'archived') AS asset_count,
             (SELECT COUNT(*) FROM media_asset WHERE owner_id = %s AND visibility = 'public' AND import_status = 'active') AS public_asset_count,
             (SELECT COUNT(*) FROM work WHERE owner_id = %s AND work_status <> 'archived') AS work_count,
             (SELECT COUNT(*) FROM work WHERE owner_id = %s AND visibility = 'public' AND work_status = 'ready') AS publishable_work_count""",
        (g.user_id, g.user_id, g.user_id, g.user_id),
    )
    return success(row)


@bp.get("/works")
@login_required
def works():
    status = request.args.get("status")
    if status == "archived":
        status_clause = "w.work_status = 'archived'"
    else:
        status_clause = "w.work_status <> 'archived'"
    rows = query(
        f"""SELECT w.*,
                  (SELECT COUNT(*) FROM work_media wm WHERE wm.work_id = w.work_id) AS asset_count,
                  (SELECT COUNT(*) FROM work_media wm WHERE wm.work_id = w.work_id AND wm.is_public) AS public_asset_count
             FROM work w
            WHERE w.owner_id = %s AND {status_clause}
            ORDER BY w.updated_at DESC, w.work_id DESC""",
        (g.user_id,),
    )
    return success(rows)


@bp.post("/works")
@login_required
def create():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    if not title:
        return error("title is required")
    if not description:
        return error("description is required")
    execute(
        """INSERT INTO work
           (owner_id, title, description, work_type, visibility, work_status,
            content_type, cover_mode, summary, body)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            g.user_id,
            title,
            description,
            payload.get("work_type") or "other",
            payload.get("visibility") or "public",
            payload.get("work_status") or "ready",
            payload.get("content_type") or "auto",
            payload.get("cover_mode") or "auto",
            payload.get("summary"),
            payload.get("body"),
        ),
    )
    work_id = query_one("SELECT LAST_INSERT_ID() AS id")["id"]
    return success(get_work(work_id), msg="work created")


@bp.get("/works/<int:work_id>")
@login_required
def detail(work_id):
    work = get_work(work_id)
    if not work:
        return error("work not found", http_status=404)
    return success(work)


@bp.patch("/works/<int:work_id>")
@login_required
def update(work_id):
    if not get_work(work_id):
        return error("work not found", http_status=404)
    payload = request.get_json(silent=True) or {}
    if "description" in payload and not str(payload.get("description") or "").strip():
        return error("description is required")
    allowed = {
        "title",
        "description",
        "work_type",
        "visibility",
        "work_status",
        "content_type",
        "cover_mode",
        "cover_asset_id",
        "summary",
        "body",
    }
    aliases = {"content_status": "work_status"}
    assignments = []
    params = []
    for key, value in payload.items():
        field = aliases.get(key, key)
        if field in allowed:
            if field == "cover_asset_id" and value in ("", None):
                value = None
            assignments.append(f"{field} = %s")
            params.append(value)
    if assignments:
        params.extend([work_id, g.user_id])
        execute(
            f"UPDATE work SET {', '.join(assignments)} WHERE work_id = %s AND owner_id = %s",
            params,
        )
    return success(get_work(work_id), msg="work updated")


@bp.post("/works/<int:work_id>/assets")
@login_required
def attach_asset(work_id):
    if not get_work(work_id):
        return error("work not found", http_status=404)
    payload = request.get_json(silent=True) or {}
    asset_id = payload.get("asset_id")
    asset = query_one(
        "SELECT asset_id FROM media_asset WHERE owner_id = %s AND asset_id = %s",
        (g.user_id, asset_id),
    )
    if not asset:
        return error("asset not found", http_status=404)
    execute(
        """INSERT INTO work_media (work_id, asset_id, role, display_order, is_public)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE
             role = VALUES(role),
             display_order = VALUES(display_order),
             is_public = VALUES(is_public)""",
        (
            work_id,
            asset_id,
            payload.get("role") or "main",
            int(payload.get("display_order") or 0),
            bool(payload.get("is_public", True)),
        ),
    )
    return success(get_work(work_id), msg="asset attached")


@bp.patch("/works/<int:work_id>/assets/<int:asset_id>")
@login_required
def update_asset_link(work_id, asset_id):
    payload = request.get_json(silent=True) or {}
    assignments = []
    params = []
    for field in ("role", "display_order", "is_public"):
        if field in payload:
            assignments.append(f"{field} = %s")
            params.append(payload[field])
    if assignments:
        params.extend([work_id, asset_id])
        execute(
            f"UPDATE work_media SET {', '.join(assignments)} WHERE work_id = %s AND asset_id = %s",
            params,
        )
    return success(get_work(work_id), msg="asset link updated")


@bp.delete("/works/<int:work_id>/assets/<int:asset_id>")
@login_required
def detach_asset(work_id, asset_id):
    execute("DELETE FROM work_media WHERE work_id = %s AND asset_id = %s", (work_id, asset_id))
    return success(msg="asset detached")


@bp.post("/works/<int:work_id>/assets/<int:asset_id>/extract-text")
@login_required
def extract_asset_text_to_work(work_id, asset_id):
    work = get_work(work_id)
    if not work:
        return error("work not found", http_status=404)
    asset = query_one(
        """SELECT a.*
             FROM work_media wm
             JOIN media_asset a ON a.asset_id = wm.asset_id
            WHERE wm.work_id = %s AND wm.asset_id = %s AND a.owner_id = %s""",
        (work_id, asset_id, g.user_id),
    )
    if not asset:
        return error("asset is not attached to this work", http_status=404)
    candidate = asset.get("local_path") or asset.get("public_export_path")
    text, reason = extract_asset_text(candidate, asset.get("mime_type"), asset.get("asset_name"))
    if not text:
        return error(reason or "no text could be extracted")
    execute(
        """UPDATE work
              SET body = %s,
                  summary = COALESCE(NULLIF(summary, ''), %s)
            WHERE work_id = %s AND owner_id = %s""",
        (text, summarize_text(text), work_id, g.user_id),
    )
    return success(get_work(work_id), msg="asset text copied to work body")


@bp.post("/works/<int:work_id>/archive")
@login_required
def archive_work(work_id):
    affected = execute(
        "UPDATE work SET work_status = 'archived' WHERE work_id = %s AND owner_id = %s",
        (work_id, g.user_id),
    )
    if not affected:
        return error("work not found", http_status=404)
    return success(msg="work archived")


@bp.post("/works/<int:work_id>/restore")
@login_required
def restore_work(work_id):
    affected = execute(
        "UPDATE work SET work_status = 'draft' WHERE work_id = %s AND owner_id = %s",
        (work_id, g.user_id),
    )
    if not affected:
        return error("work not found", http_status=404)
    return success(get_work(work_id), msg="work restored")


@bp.delete("/works/<int:work_id>")
@login_required
def delete_work(work_id):
    work = get_work(work_id)
    if not work:
        return error("work not found", http_status=404)
    execute("DELETE FROM work_media WHERE work_id = %s", (work_id,))
    execute("DELETE FROM work_tag WHERE work_id = %s", (work_id,))
    affected = execute(
        "DELETE FROM work WHERE work_id = %s AND owner_id = %s",
        (work_id, g.user_id),
    )
    if not affected:
        return error("work not found", http_status=404)
    return success(msg="work deleted")
