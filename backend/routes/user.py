from flask import Blueprint, g, request

from auth import create_token, hash_password, login_required, verify_password
from db import execute, query_one
from response import error, success


bp = Blueprint("user", __name__, url_prefix="/api/user")


def user_payload(row):
    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "email": row["email"],
        "display_name": row.get("display_name") or row["username"],
        "bio": row.get("bio") or "",
        "token": create_token(row["user_id"], row["username"]),
    }


@bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    bio = payload.get("bio") or ""
    if not username or not email or not password:
        return error("username, email and password are required")

    exists = query_one(
        "SELECT user_id FROM user_account WHERE username = %s OR email = %s",
        (username, email),
    )
    if exists:
        return error("username or email already exists")

    execute(
        """INSERT INTO user_account (username, email, password_hash, last_login_at)
           VALUES (%s, %s, %s, NOW())""",
        (username, email, hash_password(password)),
    )
    user_id = query_one("SELECT LAST_INSERT_ID() AS id")["id"]
    execute(
        """INSERT INTO creator_profile (user_id, display_name, bio, homepage_config)
           VALUES (%s, %s, %s, JSON_OBJECT('layout', JSON_ARRAY()))""",
        (user_id, username, bio),
    )
    row = query_one(
        """SELECT u.user_id, u.username, u.email, p.display_name, p.bio
             FROM user_account u
             JOIN creator_profile p ON p.user_id = u.user_id
            WHERE u.user_id = %s""",
        (user_id,),
    )
    return success(user_payload(row), msg="account created")


@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    row = query_one(
        """SELECT u.user_id, u.username, u.email, u.password_hash, p.display_name, p.bio
             FROM user_account u
             LEFT JOIN creator_profile p ON p.user_id = u.user_id
            WHERE u.username = %s AND u.account_status = 'active'""",
        (username,),
    )
    if not row or not verify_password(password, row["password_hash"]):
        return error("invalid username or password", http_status=401)
    execute("UPDATE user_account SET last_login_at = NOW() WHERE user_id = %s", (row["user_id"],))
    return success(user_payload(row), msg="signed in")


@bp.get("/me")
@login_required
def me():
    row = query_one(
        """SELECT u.user_id, u.username, u.email, p.display_name, p.bio
             FROM user_account u
             LEFT JOIN creator_profile p ON p.user_id = u.user_id
            WHERE u.user_id = %s""",
        (g.user_id,),
    )
    if not row:
        return error("user not found", http_status=404)
    return success({k: v for k, v in user_payload(row).items() if k != "token"})
