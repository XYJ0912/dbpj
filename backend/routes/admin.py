# ============================================================
# routes/admin.py — 管理员接口
# ============================================================
# 接口清单：
#   POST /api/admin/user/<id>/deactivate   停用/注销用户（sp_deactivate_user）
#   GET  /api/admin/stats                  系统统计概览
# ============================================================

from flask import Blueprint, g

from db import query, query_one, call_proc
from auth import login_required
from response import success, error

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _is_admin():
    """检查当前用户是否有 admin 角色"""
    row = query_one(
        """SELECT 1 FROM user_role ur
           JOIN role r ON r.role_id = ur.role_id
           WHERE ur.user_id = %s AND r.role_name = 'admin'""",
        (g.user_id,),
    )
    return row is not None


# ── 停用/注销用户 ─────────────────────────────
@bp.post("/user/<int:target_id>/deactivate")
@login_required
def deactivate_user(target_id):
    """
    停用或注销用户。

    对应存储过程：sp_deactivate_user
    参数通过 query string：?mode=suspended 或 ?mode=deactivated

    suspended  → 可恢复：内容归档，资源禁用
    deactivated → 不可恢复：内容删除，授权撤销，主页冻结

    仅管理员可操作。
    """
    if not _is_admin():
        return error("仅管理员可执行此操作", http_status=403)

    from flask import request
    mode = request.args.get("mode", "suspended")

    if mode not in ("suspended", "deactivated"):
        return error("无效的模式，可选：suspended, deactivated")

    result = call_proc(
        "sp_deactivate_user",
        [target_id, mode, g.user_id],
        2,
    )
    code = result.get("out_0")
    msg = result.get("out_1", "")
    if code != 0:
        return error(msg)
    return success(msg=msg)


# ── 系统统计概览 ──────────────────────────────
@bp.get("/stats")
@login_required
def system_stats():
    """
    获取系统整体统计数据。

    仅管理员可访问。
    """
    if not _is_admin():
        return error("仅管理员可访问", http_status=403)

    stats = {}

    # 用户统计
    row = query_one(
        """SELECT
               COUNT(*) AS total,
               SUM(account_status = 'active') AS active,
               SUM(account_status = 'suspended') AS suspended,
               SUM(account_status = 'deactivated') AS deactivated
           FROM `user`"""
    )
    stats["users"] = row

    # 内容统计
    row = query_one(
        """SELECT
               COUNT(*) AS total,
               SUM(content_status = 'published') AS published,
               SUM(content_status = 'draft') AS draft,
               SUM(content_status = 'archived') AS archived,
               SUM(content_status = 'deleted') AS deleted
           FROM content"""
    )
    stats["contents"] = row

    # 互动统计
    row = query_one(
        """SELECT
               (SELECT COUNT(*) FROM like_record) AS total_likes,
               (SELECT COUNT(*) FROM comment WHERE comment_status = 'visible') AS total_comments,
               (SELECT COUNT(*) FROM favorite_record) AS total_favorites,
               (SELECT COUNT(*) FROM browse_history) AS total_browses,
               (SELECT COUNT(*) FROM follow) AS total_follows"""
    )
    stats["interactions"] = row

    # 资源授权统计
    row = query_one(
        """SELECT
               (SELECT COUNT(*) FROM user_asset WHERE asset_status = 'active') AS active_assets,
               (SELECT COUNT(*) FROM asset_authorization_request WHERE request_status = 'pending') AS pending_requests,
               (SELECT COUNT(*) FROM asset_authorization WHERE authorization_status = 'active') AS active_authorizations"""
    )
    stats["authorizations"] = row

    return success(stats)
