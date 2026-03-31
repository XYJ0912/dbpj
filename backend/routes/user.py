# ============================================================
# routes/user.py — 用户相关接口
# ============================================================

from flask import Blueprint, request, g

from db import query, query_one, execute, call_proc
from auth import hash_password, verify_password, create_token, login_required
from response import success, error, paginate_params
from services import get_user_roles, user_has_role

bp = Blueprint("user", __name__, url_prefix="/api/user")


def _build_profile(user_id):
    profile = query_one("SELECT * FROM v_user_profile WHERE user_id = %s", (user_id,))
    if not profile:
        return None

    follow_stats = query_one(
        "SELECT * FROM v_user_follow_stats WHERE user_id = %s",
        (user_id,),
    ) or {"follower_count": 0, "following_count": 0}

    content_stats = query_one(
        """SELECT
               COALESCE(SUM(content_status = 'published'), 0) AS published_content_count,
               COALESCE(SUM(content_status = 'draft'), 0) AS draft_content_count,
               COALESCE(SUM(content_status = 'archived'), 0) AS archived_content_count
           FROM content
           WHERE author_id = %s""",
        (user_id,),
    ) or {}

    profile["roles"] = get_user_roles(user_id)
    profile["follower_count"] = follow_stats.get("follower_count", 0)
    profile["following_count"] = follow_stats.get("following_count", 0)
    profile["published_content_count"] = content_stats.get("published_content_count", 0)
    profile["draft_content_count"] = content_stats.get("draft_content_count", 0)
    profile["archived_content_count"] = content_stats.get("archived_content_count", 0)
    return profile


def _tag_preference_rows(user_id, tag_type=None, limit=10):
    params = [user_id, user_id, user_id, user_id, user_id]
    type_filter = ""
    if tag_type:
        type_filter = "WHERE t.tag_type = %s"
        params.append(tag_type)
    params.append(limit)

    return query(
        f"""SELECT
                t.tag_id,
                t.tag_name,
                t.tag_type,
                t.tag_category,
                t.work_type,
                SUM(src.score) AS interaction_score
            FROM (
                SELECT ct.tag_id, 5 AS score
                  FROM content c
                  JOIN content_tag ct ON ct.content_id = c.content_id
                 WHERE c.author_id = %s
                UNION ALL
                SELECT ct.tag_id, 3 AS score
                  FROM like_record lr
                  JOIN content_tag ct ON ct.content_id = lr.content_id
                 WHERE lr.user_id = %s
                UNION ALL
                SELECT ct.tag_id, 4 AS score
                  FROM favorite_record fr
                  JOIN content_tag ct ON ct.content_id = fr.content_id
                 WHERE fr.user_id = %s
                UNION ALL
                SELECT ct.tag_id, 2 AS score
                  FROM comment cm
                  JOIN content_tag ct ON ct.content_id = cm.content_id
                 WHERE cm.author_id = %s
                   AND cm.comment_status = 'visible'
                UNION ALL
                SELECT ct.tag_id, 1 AS score
                  FROM browse_history bh
                  JOIN content_tag ct ON ct.content_id = bh.content_id
                 WHERE bh.user_id = %s
            ) src
            JOIN v_active_tag t ON t.tag_id = src.tag_id
            {type_filter}
            GROUP BY t.tag_id, t.tag_name, t.tag_type, t.tag_category, t.work_type
            ORDER BY interaction_score DESC, t.tag_name
            LIMIT %s""",
        params,
    )


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password", "")
    bio = data.get("bio")
    avatar_url = data.get("avatar_url")

    if not username or len(username) < 2:
        return error("用户名至少 2 个字符")
    if not email or "@" not in email:
        return error("邮箱格式不正确")
    if not password or len(password) < 6:
        return error("密码至少 6 位")

    result = call_proc(
        "sp_register_user",
        [username, email, hash_password(password), avatar_url, bio],
        3,
    )

    if result.get("out_1") != 0:
        return error(result.get("out_2") or "注册失败")

    token = create_token(result.get("out_0"), username)
    return success(
        {"user_id": result.get("out_0"), "username": username, "token": token},
        msg=result.get("out_2") or "注册成功",
    )


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error("用户名和密码不能为空")

    user = query_one(
        """SELECT user_id, username, password_hash, account_status
             FROM user
            WHERE username = %s""",
        (username,),
    )
    if not user:
        return error("用户不存在")
    if user["account_status"] != "active":
        return error(f"账户状态异常：{user['account_status']}")
    if not verify_password(password, user["password_hash"]):
        return error("密码错误")

    execute(
        "UPDATE user SET last_login_time = NOW() WHERE user_id = %s",
        (user["user_id"],),
    )

    token = create_token(user["user_id"], user["username"])
    return success(
        {"user_id": user["user_id"], "username": user["username"], "token": token},
        msg="登录成功",
    )


@bp.get("/me")
@login_required
def get_me():
    profile = _build_profile(g.user_id)
    if not profile:
        return error("用户不存在", http_status=404)
    return success(profile)


@bp.get("/<int:user_id>/profile")
def get_profile(user_id):
    profile = _build_profile(user_id)
    if not profile:
        return error("用户不存在", http_status=404)
    return success(profile)


@bp.get("/<int:user_id>/feed")
@login_required
def get_feed(user_id):
    if user_id != g.user_id and not user_has_role(g.user_id, {"admin"}):
        return error("只能查看自己的 Feed", http_status=403)

    page, size, offset = paginate_params()
    rows = query(
        """SELECT
               c.content_id,
               c.title,
               c.content_type,
               c.visibility,
               c.created_at,
               c.updated_at,
               c.view_count,
               c.like_count,
               c.comment_count,
               u.user_id AS author_id,
               u.username AS author_name,
               u.avatar_url AS author_avatar
           FROM follow f
           JOIN content c
             ON c.author_id = f.following_id
           JOIN user u
             ON u.user_id = c.author_id
          WHERE f.follower_id = %s
            AND c.content_status = 'published'
            AND c.visibility IN ('public', 'followers_only')
            AND u.account_status = 'active'
          ORDER BY c.created_at DESC
          LIMIT %s OFFSET %s""",
        (user_id, size, offset),
    )
    return success({"page": page, "page_size": size, "items": rows})


@bp.get("/<int:user_id>/behavior")
def get_behavior(user_id):
    profile = query_one("SELECT user_id, username FROM user WHERE user_id = %s", (user_id,))
    if not profile:
        return error("用户不存在", http_status=404)

    behavior = query_one(
        """SELECT
               COALESCE((SELECT COUNT(*) FROM content WHERE author_id = %s AND content_status = 'published'), 0) AS published_count,
               COALESCE((SELECT COUNT(*) FROM content WHERE author_id = %s AND content_status = 'draft'), 0) AS draft_count,
               COALESCE((SELECT COUNT(*) FROM comment WHERE author_id = %s AND comment_status = 'visible'), 0) AS comment_count,
               COALESCE((SELECT COUNT(*) FROM like_record WHERE user_id = %s), 0) AS likes_given,
               COALESCE((SELECT SUM(like_count) FROM content WHERE author_id = %s), 0) AS likes_received,
               COALESCE((SELECT COUNT(*) FROM favorite_record WHERE user_id = %s), 0) AS favorites_given,
               COALESCE((SELECT COUNT(*) FROM browse_history WHERE user_id = %s), 0) AS browse_count""",
        (user_id, user_id, user_id, user_id, user_id, user_id, user_id),
    ) or {}

    follow_stats = query_one(
        "SELECT follower_count, following_count FROM v_user_follow_stats WHERE user_id = %s",
        (user_id,),
    ) or {"follower_count": 0, "following_count": 0}

    behavior["user_id"] = user_id
    behavior["username"] = profile["username"]
    behavior["follower_count"] = follow_stats.get("follower_count", 0)
    behavior["following_count"] = follow_stats.get("following_count", 0)
    return success(behavior)


@bp.get("/<int:user_id>/tags")
def get_tag_preference(user_id):
    limit = min(int(request.args.get("limit", 10)), 50)
    rows = _tag_preference_rows(user_id, tag_type=None, limit=limit)
    return success(rows)


@bp.get("/<int:user_id>/works")
def get_work_preference(user_id):
    limit = min(int(request.args.get("limit", 10)), 50)
    rows = _tag_preference_rows(user_id, tag_type="work", limit=limit)
    return success(rows)


@bp.get("/<int:user_id>/friends")
def get_mutual_friends(user_id):
    rows = query(
        """SELECT
               u.user_id AS friend_id,
               u.username AS friend_name,
               u.avatar_url AS friend_avatar,
               f1.followed_at AS follow_time,
               f2.followed_at AS follow_back_time
           FROM follow f1
           JOIN follow f2
             ON f1.following_id = f2.follower_id
            AND f1.follower_id = f2.following_id
           JOIN user u
             ON u.user_id = f1.following_id
          WHERE f1.follower_id = %s
          ORDER BY GREATEST(f1.followed_at, f2.followed_at) DESC""",
        (user_id,),
    )
    return success(rows)
