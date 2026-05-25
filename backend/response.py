# ============================================================
# response.py — 统一响应格式与 JSON 序列化
# ============================================================

import datetime
import decimal
import json

from flask import Response


class CustomEncoder(json.JSONEncoder):
    """
    自定义 JSON 编码器，处理 MySQL 返回的特殊类型：
    - datetime → ISO 8601 字符串
    - Decimal  → float
    - bytes    → str
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return super().default(obj)


def success(data=None, msg="ok"):
    """成功响应"""
    body = {"code": 0, "msg": msg}
    if data is not None:
        body["data"] = data
    return Response(
        json.dumps(body, cls=CustomEncoder, ensure_ascii=False),
        mimetype="application/json; charset=utf-8",
    )


def error(msg, code=1, http_status=400):
    """业务错误响应"""
    body = {"code": code, "msg": msg}
    return Response(
        json.dumps(body, cls=CustomEncoder, ensure_ascii=False),
        status=http_status,
        mimetype="application/json; charset=utf-8",
    )


def paginate_params():
    """
    从 query string 提取分页参数。
    返回 (page, page_size, offset)

    用法：
        page, size, offset = paginate_params()
        rows = query("SELECT ... LIMIT %s OFFSET %s", (size, offset))
    """
    from flask import request, current_app

    page = max(int(request.args.get("page", 1)), 1)
    size = min(
        int(request.args.get("page_size", current_app.config.get("PAGE_SIZE_DEFAULT", 20))),
        current_app.config.get("PAGE_SIZE_MAX", 100),
    )
    offset = (page - 1) * size
    return page, size, offset
