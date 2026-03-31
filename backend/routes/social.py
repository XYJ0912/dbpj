# ============================================================
# routes/social.py — 社交与元数据接口
# ============================================================

from flask import Blueprint, request, g

from db import query, query_one, execute
from auth import login_required
from response import success, error, paginate_params

bp = Blueprint("social", __name__, url_prefix="/api")


@bp.post("/follow/<int:target_id>")
@login_required
def follow(target_id):
    if g.user_id == target_id:
        return error("不能关注自己")

    target = query_one(
        "SELECT account_status FROM user WHERE user_id = %s",
        (target_id,),
    )
    if not target:
        return error("目标用户不存在")
    if target["account_status"] != "active":
        return error("目标用户账户状态异常")

    try:
        execute(
            "INSERT INTO follow (follower_id, following_id) VALUES (%s, %s)",
            (g.user_id, target_id),
        )
    except Exception as exc:
        if "Duplicate" in str(exc):
            return error("已经关注了")
        raise

    return success(msg="关注成功")


@bp.delete("/follow/<int:target_id>")
@login_required
def unfollow(target_id):
    affected = execute(
        "DELETE FROM follow WHERE follower_id = %s AND following_id = %s",
        (g.user_id, target_id),
    )
    if affected == 0:
        return error("你还没有关注对方")
    return success(msg="已取消关注")


@bp.get("/works")
def list_works():
    page, size, offset = paginate_params()
    rows = query(
        """SELECT
               w.work_id,
               w.work_name,
               w.work_type,
               w.description,
               COUNT(DISTINCT pc.content_id) AS content_count,
               COALESCE(SUM(pc.like_count), 0) AS total_likes,
               COALESCE(SUM(pc.view_count), 0) AS total_views,
               COUNT(DISTINCT wc.character_id) AS character_count
           FROM v_work w
           LEFT JOIN v_active_content_tag act
                  ON act.tag_id = w.work_id
                 AND act.tag_type = 'work'
           LEFT JOIN v_public_content pc
                  ON pc.content_id = act.content_id
           LEFT JOIN v_work_character wc
                  ON wc.work_id = w.work_id
           WHERE w.work_status = 'active'
           GROUP BY w.work_id, w.work_name, w.work_type, w.description
           ORDER BY total_likes DESC, total_views DESC, w.work_name
           LIMIT %s OFFSET %s""",
        (size, offset),
    )
    return success({"page": page, "page_size": size, "items": rows})


@bp.get("/works/<int:work_id>")
def work_detail(work_id):
    work = query_one(
        """SELECT *
             FROM v_work
            WHERE work_id = %s
              AND work_status = 'active'""",
        (work_id,),
    )
    if not work:
        return error("作品不存在", http_status=404)

    characters = query(
        """SELECT
               atr.target_tag_id AS character_id,
               atr.target_tag_name AS character_name,
               atr.role_in_relation AS role_in_work
           FROM v_active_tag_relation atr
          WHERE atr.relation_type = 'work_contains_character'
            AND atr.source_tag_id = %s
          ORDER BY atr.target_tag_name""",
        (work_id,),
    )

    page, size, offset = paginate_params()
    contents = query(
        """SELECT
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

    work["characters"] = characters
    work["contents"] = {"page": page, "page_size": size, "items": contents}
    return success(work)


@bp.get("/characters")
def list_characters():
    page, size, offset = paginate_params()
    rows = query(
        """SELECT
               ch.character_id,
               ch.character_name,
               ch.description,
               COUNT(DISTINCT pc.content_id) AS content_count,
               COALESCE(SUM(pc.like_count), 0) AS total_likes,
               COALESCE(SUM(pc.view_count), 0) AS total_views,
               COUNT(DISTINCT wc.work_id) AS work_count
           FROM v_character ch
           LEFT JOIN v_active_content_tag act
                  ON act.tag_id = ch.character_id
                 AND act.tag_type = 'character'
           LEFT JOIN v_public_content pc
                  ON pc.content_id = act.content_id
           LEFT JOIN v_work_character wc
                  ON wc.character_id = ch.character_id
           WHERE ch.character_status = 'active'
           GROUP BY ch.character_id, ch.character_name, ch.description
           ORDER BY total_likes DESC, total_views DESC, ch.character_name
           LIMIT %s OFFSET %s""",
        (size, offset),
    )
    return success({"page": page, "page_size": size, "items": rows})


@bp.get("/tags")
def list_tags():
    tag_type = request.args.get("tag_type")
    category = request.args.get("category")
    include_inactive = request.args.get("include_inactive") == "1"

    conditions = []
    params = []
    if not include_inactive:
        conditions.append("tag_status = 'active'")
    if tag_type:
        conditions.append("tag_type = %s")
        params.append(tag_type)
    if category:
        conditions.append("tag_category = %s")
        params.append(category)

    where_sql = ""
    if conditions:
        where_sql = "WHERE " + " AND ".join(conditions)

    rows = query(
        f"""SELECT
                tag_id, tag_name, tag_type, tag_category, parent_tag_id,
                description, work_type, created_by, tag_status, merged_into_tag_id, created_at
            FROM tag
            {where_sql}
            ORDER BY tag_type, tag_category, tag_name""",
        params,
    )
    return success(rows)
