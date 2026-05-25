import json
import os
import re
import shutil
from pathlib import Path

from config import Config
from db import execute, query, query_one
from file_services import contains_local_path, public_asset_url
from services import parse_json_value


EXPORT_ROOT = Path(Config.EXPORT_ROOT).resolve() if Config.EXPORT_ROOT else Path(__file__).resolve().parents[1] / "exports"
TEMPLATE_DIR = Path(__file__).resolve().parent / "static_site_template"


def _selected_content_ids(user_id, payload):
    ids = payload.get("content_ids") or []
    if ids:
        return [int(item) for item in ids if int(item) > 0]
    rows = query(
        """SELECT content_id
             FROM content
            WHERE author_id = %s
              AND content_status = 'published'
              AND visibility = 'public'
            ORDER BY updated_at DESC, content_id DESC""",
        (user_id,),
    )
    return [row["content_id"] for row in rows]


def collect_publishable_content(user_id, payload):
    content_ids = _selected_content_ids(user_id, payload)
    if not content_ids:
        return []
    placeholders = ", ".join(["%s"] * len(content_ids))
    works = query(
        f"""SELECT c.content_id, c.author_id, c.title, c.body, c.content_type,
                   c.content_status, c.visibility, c.created_at, c.updated_at
              FROM content c
             WHERE c.author_id = %s
               AND c.content_id IN ({placeholders})
             ORDER BY c.updated_at DESC, c.content_id DESC""",
        [user_id, *content_ids],
    )
    for work in works:
        work["tags"] = query(
            """SELECT t.tag_id, t.tag_name, t.tag_type
                 FROM content_tag ct
                 JOIN tag t ON t.tag_id = ct.tag_id
                WHERE ct.content_id = %s AND t.tag_status = 'active'
                ORDER BY t.tag_type, t.tag_name""",
            (work["content_id"],),
        )
        work["assets"] = query(
            """SELECT cm.role, cm.is_public, cm.display_order, a.*
                 FROM content_media cm
                 JOIN v_workspace_asset a ON a.media_id = cm.media_id
                WHERE cm.content_id = %s
                ORDER BY cm.display_order, cm.media_id""",
            (work["content_id"],),
        )
    return works


def get_homepage_config(user_id):
    row = query_one(
        "SELECT homepage_config FROM user_homepage WHERE user_id = %s",
        (user_id,),
    )
    return parse_json_value(row.get("homepage_config") if row else None, {"layout": []})


def build_public_payload(user_id, request_payload):
    works = collect_publishable_content(user_id, request_payload)
    homepage_config = get_homepage_config(user_id)
    user = query_one(
        "SELECT user_id, username, avatar_url, bio FROM user WHERE user_id = %s",
        (user_id,),
    )

    public_works = []
    all_tags = {}
    for work in works:
        public_media = []
        cover = None
        for asset in work["assets"]:
            if not asset.get("is_public"):
                continue
            public_url = public_asset_url(asset)
            media_item = {
                "media_id": asset["media_id"],
                "media_type": asset["media_type"],
                "public_url": public_url,
                "width": asset.get("width"),
                "height": asset.get("height"),
                "duration": asset.get("duration"),
                "role": asset.get("role"),
                "_checks": {
                    "visibility": asset.get("visibility"),
                    "authorization_status": asset.get("authorization_status"),
                    "thumbnail_path": asset.get("thumbnail_path"),
                    "local_path": asset.get("local_path"),
                    "file_size": asset.get("file_size"),
                },
            }
            if asset.get("role") == "cover" and not cover:
                cover = public_url
            public_media.append(media_item)

        tag_names = []
        for tag in work["tags"]:
            tag_names.append(tag["tag_name"])
            all_tags[tag["tag_id"]] = tag

        public_works.append(
            {
                "content_id": work["content_id"],
                "title": work["title"],
                "body": work.get("body"),
                "content_type": work["content_type"],
                "tags": tag_names,
                "cover": cover or (public_media[0]["public_url"] if public_media else None),
                "media": public_media,
                "_checks": {
                    "visibility": work.get("visibility"),
                    "content_status": work.get("content_status"),
                },
            }
        )

    return {
        "profile": {
            "user_id": user["user_id"],
            "username": user["username"],
            "avatar_url": user.get("avatar_url"),
            "bio": user.get("bio"),
        },
        "homepage": homepage_config,
        "works": public_works,
        "tags": list(all_tags.values()),
    }


def run_publish_checks(payload):
    items = []

    if not payload.get("homepage", {}).get("layout"):
        items.append(
            {
                "check_type": "missing_homepage_layout",
                "severity": "warning",
                "message": "主页配置缺少 layout，静态页将使用默认布局",
            }
        )

    serialized = json.dumps(_strip_internal_fields(payload), ensure_ascii=False)
    if contains_local_path(serialized):
        items.append(
            {
                "check_type": "local_path_leak",
                "severity": "error",
                "message": "公开 payload 中检测到本地绝对路径",
            }
        )

    for work in payload.get("works", []):
        if work.get("_checks", {}).get("visibility") != "public":
            items.append(
                {
                    "check_type": "private_work_included",
                    "severity": "error",
                    "message": f"作品 {work['content_id']} 不是 public 状态",
                    "related_table": "content",
                    "related_id": work["content_id"],
                }
            )
        for media in work.get("media", []):
            checks = media.get("_checks", {})
            status = checks.get("authorization_status") or "unknown"
            if checks.get("visibility") != "public":
                items.append(
                    {
                        "check_type": "private_asset_included",
                        "severity": "error",
                        "message": f"资产 {media['media_id']} 不是 public 状态",
                        "related_table": "media_asset",
                        "related_id": media["media_id"],
                    }
                )
            if status == "restricted":
                items.append(
                    {
                        "check_type": "restricted_asset_included",
                        "severity": "error",
                        "message": f"资产 {media['media_id']} 禁止公开",
                        "related_table": "media_asset",
                        "related_id": media["media_id"],
                    }
                )
            if status == "unknown":
                items.append(
                    {
                        "check_type": "unknown_license_included",
                        "severity": "warning",
                        "message": f"资产 {media['media_id']} 授权状态未确认",
                        "related_table": "media_asset",
                        "related_id": media["media_id"],
                    }
                )
            if media.get("media_type") in ("image", "gif") and not checks.get("thumbnail_path") and not media.get("public_url"):
                items.append(
                    {
                        "check_type": "missing_thumbnail",
                        "severity": "warning",
                        "message": f"资产 {media['media_id']} 缺少缩略图或公开路径",
                        "related_table": "media_asset",
                        "related_id": media["media_id"],
                    }
                )

    error_count = sum(1 for item in items if item["severity"] == "error")
    warning_count = sum(1 for item in items if item["severity"] == "warning")
    return {
        "can_publish": error_count == 0,
        "summary": {
            "works": len(payload.get("works", [])),
            "assets": sum(len(work.get("media", [])) for work in payload.get("works", [])),
            "warnings": warning_count,
            "errors": error_count,
        },
        "items": items,
    }


def _strip_internal_fields(payload):
    clean = json.loads(json.dumps(payload, ensure_ascii=False))
    for work in clean.get("works", []):
        work.pop("_checks", None)
        for media in work.get("media", []):
            media.pop("_checks", None)
    return clean


def public_payload(payload):
    return _strip_internal_fields(payload)


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def create_snapshot(user_id, request_payload):
    payload = build_public_payload(user_id, request_payload)
    report = run_publish_checks(payload)
    if not report["can_publish"] and not request_payload.get("force"):
        return {"snapshot": None, "payload": _strip_internal_fields(payload), "report": report}

    clean_payload = _strip_internal_fields(payload)
    snapshot_name = request_payload.get("snapshot_name") or "creator-homepage"
    execute(
        """INSERT INTO publish_snapshot
           (user_id, snapshot_name, output_dir, homepage_config, public_data, status)
           VALUES (%s, %s, %s, %s, %s, 'draft')""",
        (
            user_id,
            snapshot_name,
            "",
            json.dumps(clean_payload.get("homepage", {}), ensure_ascii=False),
            json.dumps(clean_payload, ensure_ascii=False),
        ),
    )
    snapshot_id = query_one("SELECT LAST_INSERT_ID() AS snapshot_id")["snapshot_id"]
    output_dir = export_static_site(snapshot_id, clean_payload, report)
    package_size = directory_size(output_dir)

    execute(
        """UPDATE publish_snapshot
              SET output_dir = %s, status = 'generated', package_size_bytes = %s
            WHERE snapshot_id = %s""",
        (str(output_dir), package_size, snapshot_id),
    )
    for work in clean_payload.get("works", []):
        execute(
            """INSERT INTO publish_item (snapshot_id, item_type, item_id, public_url)
               VALUES (%s, 'content', %s, %s)""",
            (snapshot_id, work["content_id"], work.get("cover")),
        )
        for media in work.get("media", []):
            execute(
                """INSERT IGNORE INTO publish_item (snapshot_id, item_type, item_id, public_url)
                   VALUES (%s, 'media', %s, %s)""",
                (snapshot_id, media["media_id"], media.get("public_url")),
            )
    for item in report["items"]:
        execute(
            """INSERT INTO publish_report
               (snapshot_id, check_type, severity, message, related_table, related_id)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                snapshot_id,
                item["check_type"],
                item["severity"],
                item["message"],
                item.get("related_table"),
                item.get("related_id"),
            ),
        )
    snapshot = query_one("SELECT * FROM publish_snapshot WHERE snapshot_id = %s", (snapshot_id,))
    return {"snapshot": snapshot, "payload": clean_payload, "report": report}


def export_static_site(snapshot_id, payload, report):
    output_dir = EXPORT_ROOT / f"snapshot-{snapshot_id}"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if TEMPLATE_DIR.exists():
        for item in TEMPLATE_DIR.iterdir():
            target = output_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
    (output_dir / "assets" / "media").mkdir(parents=True, exist_ok=True)
    (output_dir / "assets" / "thumbs").mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    _write_json(data_dir / "profile.json", payload.get("profile", {}))
    _write_json(data_dir / "works.json", payload.get("works", []))
    _write_json(data_dir / "tags.json", payload.get("tags", []))
    _write_json(data_dir / "homepage.json", payload.get("homepage", {}))
    _write_json(data_dir / "publish_report.json", report)
    return output_dir


def directory_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def list_snapshots(user_id):
    return query(
        """SELECT *
             FROM v_publish_report_summary
            WHERE user_id = %s
            ORDER BY created_at DESC, snapshot_id DESC""",
        (user_id,),
    )


def get_snapshot(user_id, snapshot_id):
    snapshot = query_one(
        "SELECT * FROM publish_snapshot WHERE user_id = %s AND snapshot_id = %s",
        (user_id, snapshot_id),
    )
    if not snapshot:
        return None
    snapshot["public_data"] = json.loads(snapshot["public_data"]) if isinstance(snapshot.get("public_data"), str) else snapshot.get("public_data")
    snapshot["homepage_config"] = json.loads(snapshot["homepage_config"]) if isinstance(snapshot.get("homepage_config"), str) else snapshot.get("homepage_config")
    snapshot["items"] = query("SELECT * FROM publish_item WHERE snapshot_id = %s", (snapshot_id,))
    snapshot["report"] = query("SELECT * FROM publish_report WHERE snapshot_id = %s", (snapshot_id,))
    return snapshot
