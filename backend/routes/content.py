# ============================================================
# routes/content.py — 内容相关接口
# ============================================================

import json

from flask import Blueprint, request, g

from db import query, query_one, execute, call_proc
from auth import login_required, optional_login
from response import success, error, paginate_params
from services import (
    assemble_content_detail,
    can_view_content,
    fetch_content_base,
    merge_tag_ids,
    normalize_id_list,
)

bp = Blueprint("content", __name__, url_prefix="/api/content")


def _visible_published_content_or_404(content_id, viewer_id=None):
    row = fetch_content_base(content_id)
    if not row:
        return None
    if row["content_status"] != "published":
        return None
    if not can_view_content(row, viewer_id, allow_owner_unpublished=False):
        return None
    return row


@bp.get("/hot")
def hot_content():
    page, size, offset = paginate_params()
    rows = query(
        """SELECT
               c.content_id,
               c.title,
               c.content_type,
               c.visibility,
               c.created_at,
               c.view_count,
               c.like_count,
               c.comment_count,
               u.user_id AS author_id,
               u.username AS author_name,
               u.avatar_url AS author_avatar,
               ROUND(
                   c.like_count * 3
                 + c.comment_count * 2
                 + c.view_count * 0.1
                 + CASE
                       WHEN c.created_at >= NOW() - INTERVAL 24 HOUR THEN 500
                       WHEN c.created_at >= NOW() - INTERVAL 72 HOUR THEN 200
                       WHEN c.created_at >= NOW() - INTERVAL 7 DAY THEN 50
                       ELSE 0
                   END,
                   2
               ) AS hot_score
           FROM content c
           JOIN user u ON u.user_id = c.author_id
          WHERE c.content_status = 'published'
            AND c.visibility = 'public'
            AND u.account_status = 'active'
          ORDER BY hot_score DESC, c.created_at DESC
          LIMIT %s OFFSET %s""",
        (size, offset),
    )
    return success({"page": page, "page_size": size, "items": rows})


@bp.get("/top-liked")
def top_liked():
    page, size, offset = paginate_params()
    rows = query(
        """SELECT
               c.content_id,
               c.title,
               c.content_type,
               c.created_at,
               c.like_count,
               c.comment_count,
               c.view_count,
               u.user_id AS author_id,
               u.username AS author_name
           FROM content c
           JOIN user u ON u.user_id = c.author_id
          WHERE c.content_status = 'published'
            AND c.visibility = 'public'
            AND u.account_status = 'active'
          ORDER BY c.like_count DESC, c.created_at DESC
          LIMIT %s OFFSET %s""",
        (size, offset),
    )
    return success({"page": page, "page_size": size, "items": rows})


@bp.get("/top-favorited")
def top_favorited():
    page, size, offset = paginate_params()
    rows = query(
        """SELECT
               c.content_id,
               c.title,
               c.content_type,
               c.created_at,
               c.like_count,
               c.view_count,
               u.user_id AS author_id,
               u.username AS author_name,
               COUNT(fr.user_id) AS favorite_count
           FROM content c
           JOIN user u ON u.user_id = c.author_id
           LEFT JOIN favorite_record fr ON fr.content_id = c.content_id
          WHERE c.content_status = 'published'
            AND c.visibility = 'public'
            AND u.account_status = 'active'
          GROUP BY c.content_id, c.title, c.content_type, c.created_at,
                   c.like_count, c.view_count, u.user_id, u.username
          ORDER BY favorite_count DESC, c.created_at DESC
          LIMIT %s OFFSET %s""",
        (size, offset),
    )
    return success({"page": page, "page_size": size, "items": rows})


@bp.get("/by-tag")
def by_tag():
    tag_id = request.args.get("tag_id", type=int)
    tag_name = (request.args.get("tag_name") or "").strip()
    if not tag_id and not tag_name:
        return error("请提供 tag_id 或 tag_name 参数")

    page, size, offset = paginate_params()
    if tag_id:
        tag_filter_sql = "act.tag_id = %s"
        params = [tag_id]
    else:
        tag_filter_sql = "act.tag_name = %s"
        params = [tag_name]

    rows = query(
        f"""SELECT
                act.tag_id,
                act.tag_name,
                act.tag_type,
                act.tag_category,
                pc.content_id,
                pc.title,
                pc.content_type,
                pc.created_at,
                pc.like_count,
                pc.comment_count,
                pc.view_count,
                u.user_id AS author_id,
                u.username AS author_name
            FROM v_active_content_tag act
            JOIN v_public_content pc ON pc.content_id = act.content_id
            JOIN user u ON u.user_id = pc.author_id
           WHERE {tag_filter_sql}
           ORDER BY pc.created_at DESC
           LIMIT %s OFFSET %s""",
        (*params, size, offset),
    )
    return success(
        {
            "tag_id": tag_id,
            "tag_name": tag_name or (rows[0]["tag_name"] if rows else None),
            "page": page,
            "page_size": size,
            "items": rows,
        }
    )


@bp.get("/by-work")
def by_work():
    work_id = request.args.get("work_id", type=int)
    if not work_id:
        return error("请提供 work_id 参数")

    page, size, offset = paginate_params()
    rows = query(
        """SELECT
               act.tag_id AS work_id,
               act.tag_name AS work_name,
               pc.content_id,
               pc.title,
               pc.content_type,
               pc.created_at,
               pc.like_count,
               pc.comment_count,
               pc.view_count,
               u.user_id AS author_id,
               u.username AS author_name
           FROM v_active_content_tag act
           JOIN v_public_content pc ON pc.content_id = act.content_id
           JOIN user u ON u.user_id = pc.author_id
          WHERE act.tag_id = %s
            AND act.tag_type = 'work'
          ORDER BY pc.created_at DESC
          LIMIT %s OFFSET %s""",
        (work_id, size, offset),
    )
    return success({"work_id": work_id, "page": page, "page_size": size, "items": rows})


@bp.get("/<int:content_id>")
@optional_login
def detail(content_id):
    row = assemble_content_detail(content_id, g.user_id, allow_owner_unpublished=True)
    if not row:
        return error("内容不存在或无权查看", http_status=404)
    return success(row)


@bp.get("/<int:content_id>/comments")
@optional_login
def comments(content_id):
    content = _visible_published_content_or_404(content_id, g.user_id)
    if not content:
        return error("内容不存在或无权查看", http_status=404)

    rows = query(
        """SELECT
               c.comment_id,
               c.content_id,
               c.author_id,
               u.username AS author_name,
               u.avatar_url AS author_avatar,
               c.parent_comment_id,
               c.comment_text,
               c.created_at,
               c.comment_status
           FROM comment c
           JOIN user u ON u.user_id = c.author_id
          WHERE c.content_id = %s
            AND c.comment_status = 'visible'
          ORDER BY c.created_at ASC""",
        (content_id,),
    )
    return success(rows)


@bp.post("")
@login_required
def publish():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = data.get("body", "")
    content_type = data.get("content_type", "text")
    visibility = data.get("visibility", "public")
    content_id = data.get("content_id") or data.get("draft_content_id")
    tag_ids = merge_tag_ids(data)
    media_ids = normalize_id_list(data.get("media_ids") or [])

    if not title:
        return error("标题不能为空")
    if content_type not in ("text", "image_post", "video_post", "mixed"):
        return error("无效的内容类型")
    if visibility not in ("public", "followers_only", "private"):
        return error("无效的可见性")

    result = call_proc(
        "sp_publish_content",
        [
            int(content_id) if content_id else None,
            g.user_id,
            title,
            body,
            content_type,
            visibility,
            json.dumps(tag_ids),
            json.dumps(media_ids),
        ],
        3,
    )

    if result.get("out_1") != 0:
        return error(result.get("out_2") or "内容发布失败")

    return success(
        {"content_id": result.get("out_0")},
        msg=result.get("out_2") or "内容发布成功",
    )


@bp.post("/<int:content_id>/like")
@login_required
def like(content_id):
    if not _visible_published_content_or_404(content_id, g.user_id):
        return error("内容不存在或无权操作", http_status=404)

    try:
        execute(
            "INSERT INTO like_record (user_id, content_id) VALUES (%s, %s)",
            (g.user_id, content_id),
        )
    except Exception as exc:
        if "Duplicate" in str(exc):
            return error("已经点过赞了")
        raise
    return success(msg="点赞成功")


@bp.delete("/<int:content_id>/like")
@login_required
def unlike(content_id):
    affected = execute(
        "DELETE FROM like_record WHERE user_id = %s AND content_id = %s",
        (g.user_id, content_id),
    )
    if affected == 0:
        return error("你还没有点赞过")
    return success(msg="已取消点赞")


@bp.post("/<int:content_id>/favorite")
@login_required
def favorite(content_id):
    if not _visible_published_content_or_404(content_id, g.user_id):
        return error("内容不存在或无权操作", http_status=404)

    try:
        execute(
            "INSERT INTO favorite_record (user_id, content_id) VALUES (%s, %s)",
            (g.user_id, content_id),
        )
    except Exception as exc:
        if "Duplicate" in str(exc):
            return error("已经收藏过了")
        raise
    return success(msg="收藏成功")


@bp.delete("/<int:content_id>/favorite")
@login_required
def unfavorite(content_id):
    affected = execute(
        "DELETE FROM favorite_record WHERE user_id = %s AND content_id = %s",
        (g.user_id, content_id),
    )
    if affected == 0:
        return error("你还没有收藏过")
    return success(msg="已取消收藏")


@bp.post("/<int:content_id>/comment")
@login_required
def add_comment(content_id):
    if not _visible_published_content_or_404(content_id, g.user_id):
        return error("内容不存在或无权评论", http_status=404)

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    parent_id = data.get("parent_comment_id")

    if not text:
        return error("评论内容不能为空")

    if parent_id:
        parent = query_one(
            """SELECT comment_id, content_id, parent_comment_id
                 FROM comment
                WHERE comment_id = %s""",
            (parent_id,),
        )
        if not parent or parent["content_id"] != content_id:
            return error("父评论不存在")
        if parent["parent_comment_id"] is not None:
            return error("仅支持两层评论结构")

    execute(
        """INSERT INTO comment (content_id, author_id, parent_comment_id, comment_text)
           VALUES (%s, %s, %s, %s)""",
        (content_id, g.user_id, parent_id, text),
    )
    return success(msg="评论成功")


@bp.post("/<int:content_id>/browse")
@optional_login
def browse(content_id):
    if not _visible_published_content_or_404(content_id, g.user_id):
        return error("内容不存在或无权查看", http_status=404)

    if not g.user_id:
        return success(msg="浏览成功（未登录，不记录历史）")

    data = request.get_json(silent=True) or {}
    duration = data.get("duration_seconds")
    execute(
        """INSERT INTO browse_history (user_id, content_id, duration_seconds)
           VALUES (%s, %s, %s)""",
        (g.user_id, content_id, duration),
    )
    return success(msg="浏览已记录")


@bp.put("/<int:content_id>/archive")
@login_required
def archive(content_id):
    result = call_proc(
        "sp_delete_or_archive_content",
        [content_id, g.user_id, "archive"],
        2,
    )
    if result.get("out_0") != 0:
        return error(result.get("out_1") or "归档失败")
    return success(msg=result.get("out_1") or "内容已归档")


@bp.delete("/<int:content_id>")
@login_required
def delete_content(content_id):
    mode = request.args.get("mode", "soft_delete")
    if mode != "soft_delete":
        return error("当前数据库版本仅支持 soft_delete")

    result = call_proc(
        "sp_delete_or_archive_content",
        [content_id, g.user_id, "soft_delete"],
        2,
    )
    if result.get("out_0") != 0:
        return error(result.get("out_1") or "删除失败")
    return success(msg=result.get("out_1") or "内容已软删除")
