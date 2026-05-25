# ============================================================
# auth.py — JWT 认证工具
# ============================================================
# 设计说明：
#   - 使用 PyJWT 签发和验证 Token
#   - 提供 @login_required 装饰器，自动解析 Token 并注入 g.user_id
#   - 密码使用 hashlib 的 SHA256 做简易哈希（课程项目级别）
#   - 生产环境应替换为 bcrypt
# ============================================================

import hashlib
import datetime
from functools import wraps

import jwt
from flask import request, jsonify, g, current_app


def hash_password(password: str) -> str:
    """
    简易密码哈希（课程项目用）。
    生产环境请使用 bcrypt：
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    """
    return "$2b$12$" + hashlib.sha256(password.encode("utf-8")).hexdigest()[:40]


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码是否匹配"""
    return hash_password(password) == password_hash


def create_token(user_id: int, username: str) -> str:
    """签发 JWT Token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(hours=current_app.config["JWT_EXPIRE_HOURS"]),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """解析 JWT Token，失败返回 None"""
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required(f):
    """
    登录鉴权装饰器。
    用法：
        @app.get('/api/me')
        @login_required
        def get_me():
            user_id = g.user_id  # 由装饰器注入
            ...

    请求头格式：
        Authorization: Bearer <token>
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"code": 401, "msg": "缺少认证 Token"}), 401

        token = auth_header[7:]  # 去掉 "Bearer " 前缀
        payload = decode_token(token)
        if payload is None:
            return jsonify({"code": 401, "msg": "Token 无效或已过期"}), 401

        g.user_id = payload["user_id"]
        g.username = payload["username"]
        return f(*args, **kwargs)

    return decorated


def optional_login(f):
    """
    可选登录装饰器：有 Token 就解析，没有也放行。
    g.user_id 可能为 None。
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_token(auth_header[7:])
            if payload:
                g.user_id = payload["user_id"]
                g.username = payload["username"]
            else:
                g.user_id = None
                g.username = None
        else:
            g.user_id = None
            g.username = None
        return f(*args, **kwargs)

    return decorated
