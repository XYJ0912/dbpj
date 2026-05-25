import json
from datetime import datetime

from db import execute, query, query_one
from file_services import file_size, path_exists, sha256_file
from services import parse_json_value


ASSET_UPDATE_FIELDS = {
    "visibility",
    "thumbnail_path",
    "public_export_path",
    "import_status",
    "file_exists",
    "missing_reason",
    "width",
    "height",
    "duration",
    "mime_type",
}


def list_assets(user_id, media_type=None, visibility=None):
    clauses = ["uploader_id = %s"]
    params = [user_id]
    if media_type:
        clauses.append("media_type = %s")
        params.append(media_type)
    if visibility:
        clauses.append("visibility = %s")
        params.append(visibility)
    sql = "SELECT * FROM v_workspace_asset WHERE " + " AND ".join(clauses)
    sql += " ORDER BY upload_time DESC, media_id DESC"
    return query(sql, params)


def import_asset(user_id, payload):
    local_path = (payload.get("local_path") or payload.get("file_path") or "").strip()
    file_path = (payload.get("file_path") or local_path or payload.get("public_export_path") or "").strip()
    media_type = payload.get("media_type") or "image"
    storage_mode = payload.get("storage_mode") or "reference"
    exists = path_exists(local_path) if local_path else False
    size = payload.get("file_size")
    if size is None and exists:
        size = file_size(local_path)
    checksum = payload.get("checksum_sha256")
    if not checksum and exists and payload.get("hash_file"):
        checksum = sha256_file(local_path)

    execute(
        """INSERT INTO media_asset
           (uploader_id, media_type, file_path, file_size, mime_type, width, height, duration,
            storage_mode, local_path, checksum_sha256, thumbnail_path, public_export_path,
            visibility, import_status, file_exists, last_checked_at, missing_reason)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            user_id,
            media_type,
            file_path,
            size,
            payload.get("mime_type"),
            payload.get("width"),
            payload.get("height"),
            payload.get("duration"),
            storage_mode,
            local_path or None,
            checksum,
            payload.get("thumbnail_path"),
            payload.get("public_export_path"),
            payload.get("visibility") or "public",
            "active" if exists or storage_mode == "external" else "missing",
            exists or storage_mode == "external",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            None if exists or storage_mode == "external" else "文件不存在或尚未校验",
        ),
    )
    row = query_one("SELECT LAST_INSERT_ID() AS media_id")
    media_id = row["media_id"]
    upsert_license(media_id, payload)
    return get_asset(user_id, media_id)


def get_asset(user_id, media_id):
    return query_one(
        "SELECT * FROM v_workspace_asset WHERE uploader_id = %s AND media_id = %s",
        (user_id, media_id),
    )


def update_asset(user_id, media_id, payload):
    asset = get_asset(user_id, media_id)
    if not asset:
        return None
    assignments = []
    params = []
    for field in ASSET_UPDATE_FIELDS:
        if field in payload:
            assignments.append(f"{field} = %s")
            params.append(payload[field])
    if assignments:
        params.extend([media_id, user_id])
        execute(
            f"""UPDATE media_asset
                   SET {", ".join(assignments)}
                 WHERE media_id = %s AND uploader_id = %s""",
            params,
        )
    upsert_license(media_id, payload)
    return get_asset(user_id, media_id)


def upsert_license(media_id, payload):
    license_fields = {
        "authorization_status",
        "source_name",
        "source_url",
        "license_note",
        "allow_public_display",
        "allow_commercial_use",
        "attribution_required",
    }
    if not any(field in payload for field in license_fields):
        return
    execute(
        """INSERT INTO asset_license_note
           (media_id, authorization_status, source_name, source_url, license_note,
            allow_public_display, allow_commercial_use, attribution_required)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE
             authorization_status = VALUES(authorization_status),
             source_name = VALUES(source_name),
             source_url = VALUES(source_url),
             license_note = VALUES(license_note),
             allow_public_display = VALUES(allow_public_display),
             allow_commercial_use = VALUES(allow_commercial_use),
             attribution_required = VALUES(attribution_required)""",
        (
            media_id,
            payload.get("authorization_status") or "unknown",
            payload.get("source_name"),
            payload.get("source_url"),
            payload.get("license_note"),
            bool(payload.get("allow_public_display")),
            bool(payload.get("allow_commercial_use")),
            bool(payload.get("attribution_required")),
        ),
    )


def check_asset_file(user_id, media_id):
    asset = get_asset(user_id, media_id)
    if not asset:
        return None
    exists = path_exists(asset.get("local_path"))
    execute(
        """UPDATE media_asset
              SET file_exists = %s,
                  import_status = %s,
                  last_checked_at = NOW(),
                  missing_reason = %s
            WHERE media_id = %s AND uploader_id = %s""",
        (
            exists,
            "active" if exists else "missing",
            None if exists else "文件缺失或路径失效",
            media_id,
            user_id,
        ),
    )
    return get_asset(user_id, media_id)


def archive_asset(user_id, media_id):
    return execute(
        """UPDATE media_asset
              SET import_status = 'archived'
            WHERE media_id = %s AND uploader_id = %s""",
        (media_id, user_id),
    )


def workspace_overview(user_id):
    return {
        "asset_count": query_one(
            "SELECT COUNT(*) AS value FROM media_asset WHERE uploader_id = %s",
            (user_id,),
        )["value"],
        "public_asset_count": query_one(
            "SELECT COUNT(*) AS value FROM media_asset WHERE uploader_id = %s AND visibility = 'public'",
            (user_id,),
        )["value"],
        "work_count": query_one(
            "SELECT COUNT(*) AS value FROM content WHERE author_id = %s AND content_status <> 'deleted'",
            (user_id,),
        )["value"],
        "public_work_count": query_one(
            """SELECT COUNT(*) AS value FROM content
                WHERE author_id = %s AND content_status = 'published' AND visibility = 'public'""",
            (user_id,),
        )["value"],
    }


def list_works(user_id):
    return query(
        """SELECT *
             FROM v_workspace_work
            WHERE author_id = %s
            ORDER BY updated_at DESC, content_id DESC""",
        (user_id,),
    )


def create_work(user_id, payload):
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("作品标题不能为空")
    execute(
        """INSERT INTO content
           (author_id, title, body, content_type, content_status, visibility)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (
            user_id,
            title,
            payload.get("body") or "",
            payload.get("content_type") or "mixed",
            payload.get("content_status") or "published",
            payload.get("visibility") or "public",
        ),
    )
    content_id = query_one("SELECT LAST_INSERT_ID() AS content_id")["content_id"]
    return get_work(user_id, content_id)


def get_work(user_id, content_id):
    work = query_one(
        "SELECT * FROM v_workspace_work WHERE author_id = %s AND content_id = %s",
        (user_id, content_id),
    )
    if not work:
        return None
    work["assets"] = query(
        """SELECT cm.content_id, cm.media_id, cm.display_order, cm.role, cm.is_public,
                  a.*
             FROM content_media cm
             JOIN v_workspace_asset a ON a.media_id = cm.media_id
            WHERE cm.content_id = %s
            ORDER BY cm.display_order, cm.media_id""",
        (content_id,),
    )
    work["tags"] = query(
        """SELECT t.tag_id, t.tag_name, t.tag_type, t.tag_category
             FROM content_tag ct
             JOIN tag t ON t.tag_id = ct.tag_id
            WHERE ct.content_id = %s AND t.tag_status = 'active'
            ORDER BY t.tag_type, t.tag_name""",
        (content_id,),
    )
    return work


def update_work(user_id, content_id, payload):
    work = get_work(user_id, content_id)
    if not work:
        return None
    fields = []
    params = []
    for field in ("title", "body", "content_type", "content_status", "visibility"):
        if field in payload:
            fields.append(f"{field} = %s")
            params.append(payload[field])
    if fields:
        params.extend([content_id, user_id])
        execute(
            f"""UPDATE content
                   SET {", ".join(fields)}
                 WHERE content_id = %s AND author_id = %s""",
            params,
        )
    return get_work(user_id, content_id)


def attach_asset_to_work(user_id, content_id, payload):
    media_id = int(payload.get("media_id") or 0)
    if not get_work(user_id, content_id):
        raise ValueError("作品不存在")
    if not get_asset(user_id, media_id):
        raise ValueError("资产不存在")
    execute(
        """INSERT INTO content_media (content_id, media_id, display_order, role, is_public)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE
             display_order = VALUES(display_order),
             role = VALUES(role),
             is_public = VALUES(is_public)""",
        (
            content_id,
            media_id,
            payload.get("display_order") or 0,
            payload.get("role") or "main",
            bool(payload.get("is_public", True)),
        ),
    )
    return get_work(user_id, content_id)


def update_work_asset(user_id, content_id, media_id, payload):
    if not get_work(user_id, content_id):
        return None
    fields = []
    params = []
    for field in ("display_order", "role", "is_public"):
        if field in payload:
            fields.append(f"{field} = %s")
            params.append(payload[field])
    if fields:
        params.extend([content_id, media_id])
        execute(
            f"""UPDATE content_media
                   SET {", ".join(fields)}
                 WHERE content_id = %s AND media_id = %s""",
            params,
        )
    return get_work(user_id, content_id)


def detach_asset_from_work(user_id, content_id, media_id):
    if not get_work(user_id, content_id):
        return 0
    return execute(
        "DELETE FROM content_media WHERE content_id = %s AND media_id = %s",
        (content_id, media_id),
    )
