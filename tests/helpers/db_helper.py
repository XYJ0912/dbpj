from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

import pymysql
import pymysql.cursors


BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import Config  # noqa: E402


class DBHelper:
    def __init__(self):
        self.conn = pymysql.connect(
            host=os.getenv("DB_HOST", Config.DB_HOST),
            port=int(os.getenv("DB_PORT", Config.DB_PORT)),
            user=os.getenv("DB_USER", Config.DB_USER),
            password=os.getenv("DB_PASSWORD", Config.DB_PASSWORD),
            database=os.getenv("DB_NAME", Config.DB_NAME),
            charset=Config.DB_CHARSET,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def close(self):
        self.conn.close()

    def execute(self, sql: str, params: Optional[Iterable[Any]] = None) -> int:
        with self.conn.cursor() as cur:
            return cur.execute(sql, params)

    def query_one(self, sql: str, params: Optional[Iterable[Any]] = None) -> dict[str, Any] | None:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def query_all(self, sql: str, params: Optional[Iterable[Any]] = None) -> list[dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())

    def call_proc(self, proc_name: str, in_params: list[Any], out_count: int) -> dict[str, Any]:
        out_vars = [f"@_out_{i}" for i in range(out_count)]
        with self.conn.cursor() as cur:
            if out_vars:
                cur.execute("SET " + ", ".join(f"{var} = NULL" for var in out_vars))
            placeholders = ["%s"] * len(in_params) + out_vars
            cur.execute(f"CALL `{proc_name}`({', '.join(placeholders)})", in_params)
            while cur.nextset():
                pass
            if not out_vars:
                return {}
            cur.execute(f"SELECT {', '.join(out_vars)}")
            row = cur.fetchone() or {}
        return {f"out_{i}": row.get(var) for i, var in enumerate(out_vars)}

    def last_insert_id(self) -> int:
        row = self.query_one("SELECT LAST_INSERT_ID() AS id")
        return int(row["id"])

    def grant_role(self, user_id: int, role_name: str) -> None:
        role = self.query_one("SELECT role_id FROM role WHERE role_name = %s", (role_name,))
        if not role:
            raise RuntimeError(f"Role not found: {role_name}")
        self.execute(
            "INSERT IGNORE INTO user_role (user_id, role_id) VALUES (%s, %s)",
            (user_id, role["role_id"]),
        )

    def create_follow(self, follower_id: int, following_id: int) -> None:
        self.execute(
            "INSERT IGNORE INTO follow (follower_id, following_id) VALUES (%s, %s)",
            (follower_id, following_id),
        )

    def create_asset(self, owner_id: int, asset_name: str, *, asset_type: str = "background") -> int:
        self.execute(
            """INSERT INTO user_asset
               (owner_id, asset_type, asset_name, file_path, file_size, mime_type, asset_status, default_visibility)
               VALUES (%s, %s, %s, %s, %s, %s, 'active', 'authorized_only')""",
            (owner_id, asset_type, asset_name, f"/assets/test/{asset_name}.png", 12345, "image/png"),
        )
        return self.last_insert_id()

    def create_draft_content(
        self,
        author_id: int,
        title: str,
        *,
        visibility: str = "private",
        content_type: str = "text",
        body: str = "draft body",
    ) -> int:
        self.execute(
            """INSERT INTO content
               (author_id, title, body, content_type, content_status, visibility)
               VALUES (%s, %s, %s, %s, 'draft', %s)""",
            (author_id, title, body, content_type, visibility),
        )
        return self.last_insert_id()

    def get_public_work_id(self) -> int:
        row = self.query_one(
            "SELECT work_id FROM v_work WHERE work_status = 'active' ORDER BY work_id LIMIT 1"
        )
        if not row:
            raise RuntimeError("No active work found")
        return int(row["work_id"])

    def get_public_content_id(self) -> int:
        row = self.query_one(
            """SELECT content_id
                 FROM content
                WHERE content_status = 'published' AND visibility = 'public'
                ORDER BY content_id
                LIMIT 1"""
        )
        if not row:
            raise RuntimeError("No public content found")
        return int(row["content_id"])

    def find_request(self, asset_id: int, requester_id: int) -> dict[str, Any] | None:
        return self.query_one(
            """SELECT request_id, request_status, resolved_by, asset_id, requester_id
                 FROM asset_authorization_request
                WHERE asset_id = %s AND requester_id = %s
                ORDER BY request_id DESC
                LIMIT 1""",
            (asset_id, requester_id),
        )

    def find_authorization_by_request(self, request_id: int) -> dict[str, Any] | None:
        return self.query_one(
            """SELECT authorization_id, authorization_status, granted_by, grantee_id, request_id
                 FROM asset_authorization
                WHERE request_id = %s
                ORDER BY authorization_id DESC
                LIMIT 1""",
            (request_id,),
        )

    def find_latest_comment(self, author_id: int, content_id: int) -> dict[str, Any] | None:
        return self.query_one(
            """SELECT comment_id, parent_comment_id, comment_status
                 FROM comment
                WHERE author_id = %s AND content_id = %s
                ORDER BY comment_id DESC
                LIMIT 1""",
            (author_id, content_id),
        )

    def get_user_status(self, user_id: int) -> str | None:
        row = self.query_one("SELECT account_status FROM user WHERE user_id = %s", (user_id,))
        return row["account_status"] if row else None

    def get_content_status(self, content_id: int) -> str | None:
        row = self.query_one("SELECT content_status FROM content WHERE content_id = %s", (content_id,))
        return row["content_status"] if row else None

    def get_asset_status(self, asset_id: int) -> str | None:
        row = self.query_one("SELECT asset_status FROM user_asset WHERE asset_id = %s", (asset_id,))
        return row["asset_status"] if row else None

    def get_authorization_status(self, authorization_id: int) -> str | None:
        row = self.query_one(
            "SELECT authorization_status FROM asset_authorization WHERE authorization_id = %s",
            (authorization_id,),
        )
        return row["authorization_status"] if row else None

    def cleanup_user(self, user_id: int) -> None:
        asset_rows = self.query_all("SELECT asset_id FROM user_asset WHERE owner_id = %s", (user_id,))
        asset_ids = [row["asset_id"] for row in asset_rows]

        content_rows = self.query_all("SELECT content_id FROM content WHERE author_id = %s", (user_id,))
        content_ids = [row["content_id"] for row in content_rows]

        if content_ids:
            placeholders = ", ".join(["%s"] * len(content_ids))
            self.execute(f"DELETE FROM content_media WHERE content_id IN ({placeholders})", content_ids)
            self.execute(f"DELETE FROM content_tag WHERE content_id IN ({placeholders})", content_ids)
            self.execute(f"DELETE FROM comment WHERE content_id IN ({placeholders})", content_ids)
            self.execute(f"DELETE FROM like_record WHERE content_id IN ({placeholders})", content_ids)
            self.execute(f"DELETE FROM favorite_record WHERE content_id IN ({placeholders})", content_ids)
            self.execute(f"DELETE FROM browse_history WHERE content_id IN ({placeholders})", content_ids)
            self.execute(f"DELETE FROM content WHERE content_id IN ({placeholders})", content_ids)

        self.execute("DELETE FROM comment WHERE author_id = %s", (user_id,))
        self.execute("DELETE FROM like_record WHERE user_id = %s", (user_id,))
        self.execute("DELETE FROM favorite_record WHERE user_id = %s", (user_id,))
        self.execute("DELETE FROM browse_history WHERE user_id = %s", (user_id,))
        self.execute("DELETE FROM follow WHERE follower_id = %s OR following_id = %s", (user_id, user_id))

        if asset_ids:
            placeholders = ", ".join(["%s"] * len(asset_ids))
            self.execute(
                f"DELETE FROM asset_authorization WHERE asset_id IN ({placeholders}) OR grantee_id = %s OR granted_by = %s",
                [*asset_ids, user_id, user_id],
            )
            self.execute(
                f"DELETE FROM asset_authorization_request WHERE asset_id IN ({placeholders}) OR requester_id = %s OR resolved_by = %s",
                [*asset_ids, user_id, user_id],
            )
            self.execute(f"DELETE FROM user_asset WHERE asset_id IN ({placeholders})", asset_ids)
        else:
            self.execute(
                "DELETE FROM asset_authorization WHERE grantee_id = %s OR granted_by = %s",
                (user_id, user_id),
            )
            self.execute(
                "DELETE FROM asset_authorization_request WHERE requester_id = %s OR resolved_by = %s",
                (user_id, user_id),
            )

        self.execute("DELETE FROM user_role WHERE user_id = %s", (user_id,))
        self.execute("DELETE FROM user_homepage WHERE user_id = %s", (user_id,))
        self.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
