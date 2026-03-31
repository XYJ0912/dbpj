import copy
import json

from db import query, query_one


def parse_json_value(value, default=None):
    """将 MySQL JSON 字段统一解析为 Python 对象。"""
    if value is None:
        return copy.deepcopy(default)
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return copy.deepcopy(default)
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return copy.deepcopy(default)
    return copy.deepcopy(default)


def normalize_id_list(values):
    """将任意输入规整为去重后的 int 列表。"""
    result = []
    seen = set()
    for value in values or []:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number <= 0 or number in seen:
            continue
        seen.add(number)
        result.append(number)
    return result


def merge_tag_ids(payload):
    """兼容旧前端的 tag_ids/work_ids/character_ids，统一并入 tag_ids。"""
    merged = []
    merged.extend(payload.get("tag_ids") or [])
    merged.extend(payload.get("work_ids") or [])
    merged.extend(payload.get("character_ids") or [])
    return normalize_id_list(merged)


def user_has_role(user_id, role_names):
    if not user_id:
        return False
    names = list(role_names or [])
    if not names:
        return False
    placeholders = ", ".join(["%s"] * len(names))
    row = query_one(
        f"""SELECT 1
              FROM user_role ur
              JOIN role r ON r.role_id = ur.role_id
             WHERE ur.user_id = %s
               AND r.role_name IN ({placeholders})
             LIMIT 1""",
        [user_id, *names],
    )
    return row is not None


def get_user_roles(user_id):
    rows = query(
        """SELECT r.role_name
             FROM user_role ur
             JOIN role r ON r.role_id = ur.role_id
            WHERE ur.user_id = %s
            ORDER BY r.role_name""",
        (user_id,),
    )
    return [row["role_name"] for row in rows]


def fetch_content_base(content_id):
    return query_one(
        """SELECT c.content_id, c.author_id, c.title, c.body, c.content_type,
                  c.content_status, c.visibility, c.created_at, c.updated_at,
                  c.view_count, c.like_count, c.comment_count,
                  u.username AS author_name, u.avatar_url AS author_avatar,
                  u.bio AS author_bio, u.account_status AS author_status
             FROM content c
             JOIN user u ON u.user_id = c.author_id
            WHERE c.content_id = %s""",
        (content_id,),
    )


def can_view_content(content_row, viewer_id=None, allow_owner_unpublished=False):
    if not content_row:
        return False

    viewer_id = int(viewer_id) if viewer_id else None
    is_owner = viewer_id is not None and viewer_id == content_row["author_id"]

    if content_row["content_status"] == "published":
        if content_row["visibility"] == "public":
            return True
        if is_owner:
            return True
        if content_row["visibility"] == "followers_only" and viewer_id:
            row = query_one(
                """SELECT 1
                     FROM follow
                    WHERE follower_id = %s
                      AND following_id = %s
                    LIMIT 1""",
                (viewer_id, content_row["author_id"]),
            )
            return row is not None
        return False

    if allow_owner_unpublished and is_owner:
        return True
    return False


def fetch_content_tags(content_id, active_only=False):
    sql = """
        SELECT t.tag_id, t.tag_name, t.tag_type, t.tag_category,
               t.parent_tag_id, t.description, t.work_type,
               ct.tagged_at, ct.tagged_by
          FROM content_tag ct
          JOIN tag t ON t.tag_id = ct.tag_id
         WHERE ct.content_id = %s
    """
    params = [content_id]
    if active_only:
        sql += " AND t.tag_status = 'active'"
    sql += " ORDER BY t.tag_type, t.tag_name"
    return query(sql, params)


def fetch_content_media(content_id):
    return query(
        """SELECT m.media_id, m.media_type, m.file_path, m.file_size, m.mime_type,
                  m.width, m.height, m.duration, m.upload_time, cm.display_order
             FROM content_media cm
             JOIN media_asset m ON m.media_id = cm.media_id
            WHERE cm.content_id = %s
            ORDER BY cm.display_order, m.media_id""",
        (content_id,),
    )


def assemble_content_detail(content_id, viewer_id=None, allow_owner_unpublished=False):
    base = fetch_content_base(content_id)
    if not base or not can_view_content(base, viewer_id, allow_owner_unpublished):
        return None

    tags = fetch_content_tags(content_id, active_only=True)
    media_items = fetch_content_media(content_id)
    work_names = [row["tag_name"] for row in tags if row["tag_type"] == "work"]
    character_names = [row["tag_name"] for row in tags if row["tag_type"] == "character"]
    general_names = [row["tag_name"] for row in tags if row["tag_type"] == "general"]

    detail = dict(base)
    detail["tags"] = ", ".join(general_names)
    detail["works"] = ", ".join(work_names)
    detail["characters"] = ", ".join(character_names)
    detail["tag_details"] = tags
    detail["media_count"] = len(media_items)
    detail["media_items"] = media_items
    return detail


def fetch_active_tags_map(tag_ids):
    tag_ids = normalize_id_list(tag_ids)
    if not tag_ids:
        return {}
    placeholders = ", ".join(["%s"] * len(tag_ids))
    rows = query(
        f"""SELECT tag_id, tag_name, tag_type, tag_category, parent_tag_id,
                   description, work_type, created_at
              FROM v_active_tag
             WHERE tag_id IN ({placeholders})""",
        tag_ids,
    )
    return {row["tag_id"]: row for row in rows}


def fetch_visible_content_map(content_ids, viewer_id=None):
    content_ids = normalize_id_list(content_ids)
    if not content_ids:
        return {}

    placeholders = ", ".join(["%s"] * len(content_ids))
    rows = query(
        f"""SELECT c.content_id, c.author_id, c.title, c.body, c.content_type,
                   c.content_status, c.visibility, c.created_at, c.updated_at,
                   c.view_count, c.like_count, c.comment_count,
                   u.username AS author_name, u.avatar_url AS author_avatar
              FROM content c
              JOIN user u ON u.user_id = c.author_id
             WHERE c.content_id IN ({placeholders})""",
        content_ids,
    )

    result = {}
    for row in rows:
        if can_view_content(row, viewer_id, allow_owner_unpublished=False):
            result[row["content_id"]] = row
    return result
