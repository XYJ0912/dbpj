# ============================================================
# routes/authorization.py — 资源授权管理接口
# ============================================================

from flask import Blueprint, request, g

from db import query, query_one, execute, call_proc
from auth import login_required
from response import success, error

bp = Blueprint("authorization", __name__, url_prefix="/api/auth")


@bp.get("/pending")
@login_required
def pending_requests():
    rows = query(
        "SELECT * FROM v_pending_asset_request WHERE owner_id = %s ORDER BY requested_at DESC",
        (g.user_id,),
    )
    return success(rows)


@bp.get("/my-assets")
@login_required
def my_available_assets():
    rows = query(
        """SELECT
               aa.authorization_id,
               aa.asset_id,
               ua.asset_name,
               ua.asset_type,
               ua.file_path,
               ua.mime_type,
               owner.user_id AS owner_id,
               owner.username AS owner_name,
               aa.valid_from,
               aa.valid_until,
               aa.authorization_status
           FROM asset_authorization aa
           JOIN user_asset ua ON ua.asset_id = aa.asset_id
           JOIN user owner ON owner.user_id = aa.granted_by
          WHERE aa.grantee_id = %s
            AND aa.authorization_status = 'active'
            AND ua.asset_status = 'active'
            AND (aa.valid_until IS NULL OR aa.valid_until >= NOW())
          ORDER BY aa.created_at DESC""",
        (g.user_id,),
    )
    return success(rows)


@bp.get("/active-usage")
@login_required
def active_usage():
    rows = query(
        """SELECT
               aa.authorization_id,
               aa.asset_id,
               ua.asset_name,
               ua.asset_type,
               owner.user_id AS owner_id,
               owner.username AS owner_name,
               grantee.user_id AS grantee_id,
               grantee.username AS grantee_name,
               aa.valid_from,
               aa.valid_until,
               aa.authorization_status
           FROM asset_authorization aa
           JOIN user_asset ua ON ua.asset_id = aa.asset_id
           JOIN user owner ON owner.user_id = aa.granted_by
           JOIN user grantee ON grantee.user_id = aa.grantee_id
          WHERE aa.authorization_status = 'active'
            AND (aa.valid_until IS NULL OR aa.valid_until >= NOW())
            AND (aa.grantee_id = %s OR aa.granted_by = %s)
          ORDER BY aa.created_at DESC""",
        (g.user_id, g.user_id),
    )
    return success(rows)


@bp.get("/overview")
@login_required
def authorization_overview():
    rows = query(
        """SELECT
               req.request_id,
               req.request_status,
               req.request_message,
               req.requested_at,
               req.resolved_at,
               req.requester_id,
               requester.username AS requester_name,
               ua.asset_id,
               ua.asset_name,
               ua.asset_type,
               auth.authorization_id,
               auth.grantee_id,
               grantee.username AS grantee_name,
               auth.authorization_status,
               auth.valid_from,
               auth.valid_until
           FROM asset_authorization_request req
           JOIN user_asset ua ON ua.asset_id = req.asset_id
           JOIN user requester ON requester.user_id = req.requester_id
           LEFT JOIN asset_authorization auth ON auth.request_id = req.request_id
           LEFT JOIN user grantee ON grantee.user_id = auth.grantee_id
          WHERE ua.owner_id = %s
          ORDER BY req.requested_at DESC""",
        (g.user_id,),
    )
    return success(rows)


@bp.post("/request")
@login_required
def submit_request():
    data = request.get_json(silent=True) or {}
    asset_id = data.get("asset_id")
    message = data.get("message", "")

    if not asset_id:
        return error("请指定要申请的资源 asset_id")

    asset = query_one(
        """SELECT asset_id, owner_id, asset_status
             FROM user_asset
            WHERE asset_id = %s""",
        (asset_id,),
    )
    if not asset:
        return error("资源不存在", http_status=404)
    if asset["owner_id"] == g.user_id:
        return error("不能向自己申请授权")
    if asset["asset_status"] != "active":
        return error("资源当前不可申请")

    try:
        execute(
            """INSERT INTO asset_authorization_request
               (asset_id, requester_id, request_message)
               VALUES (%s, %s, %s)""",
            (asset_id, g.user_id, message),
        )
    except Exception as exc:
        if "Duplicate" in str(exc):
            return error("你已经提交过待处理申请")
        raise

    return success(msg="授权申请已提交")


@bp.post("/resolve/<int:request_id>")
@login_required
def resolve_request(request_id):
    data = request.get_json(silent=True) or {}
    decision = data.get("decision", "")
    valid_until = data.get("valid_until")

    if decision not in ("approved", "rejected"):
        return error("decision 必须为 approved 或 rejected")

    result = call_proc(
        "sp_resolve_authorization_request",
        [request_id, g.user_id, decision, valid_until],
        2,
    )
    if result.get("out_0") != 0:
        return error(result.get("out_1") or "审批失败")
    return success(msg=result.get("out_1") or "审批完成")


@bp.post("/revoke/<int:authorization_id>")
@login_required
def revoke(authorization_id):
    result = call_proc(
        "sp_revoke_authorization",
        [authorization_id, g.user_id],
        2,
    )
    if result.get("out_0") != 0:
        return error(result.get("out_1") or "撤销失败")
    return success(msg=result.get("out_1") or "授权已撤销")
