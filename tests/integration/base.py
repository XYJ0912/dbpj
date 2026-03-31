from __future__ import annotations

import os
import time
import unittest

from tests.helpers.api_client import ApiClient
from tests.helpers.db_helper import DBHelper


class LiveBackendTestCase(unittest.TestCase):
    base_url = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5000")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = ApiClient(cls.base_url)
        cls.db = DBHelper()
        cls._cleanup_user_ids: list[int] = []
        payload = cls.api.expect_plain_json("GET", "/api")
        if not isinstance(payload.get("routes"), list):
            raise AssertionError("GET /api did not return the route index")

    @classmethod
    def tearDownClass(cls):
        for user_id in reversed(cls._cleanup_user_ids):
            try:
                cls.db.cleanup_user(user_id)
            except Exception:
                pass
        cls.db.close()
        super().tearDownClass()

    @classmethod
    def register_temp_user(cls, prefix: str = "itest", *, roles: tuple[str, ...] = ()) -> dict:
        suffix = f"{int(time.time() * 1000)}_{len(cls._cleanup_user_ids)}"
        username = f"{prefix}_{suffix}"
        password = "123456"
        data = cls.api.register_user(username, password)
        user_id = int(data["user_id"])
        cls._cleanup_user_ids.append(user_id)
        for role_name in roles:
            cls.db.grant_role(user_id, role_name)
        return {
            "user_id": user_id,
            "username": username,
            "password": password,
            "token": data["token"],
            "client": cls.api.clone_with_token(data["token"]),
        }

    @classmethod
    def publish_content(
        cls,
        user: dict,
        *,
        title: str,
        visibility: str = "public",
        content_type: str = "text",
        body: str = "integration test content",
        tag_ids: list[int] | None = None,
        work_ids: list[int] | None = None,
        character_ids: list[int] | None = None,
    ) -> int:
        data = cls.api.expect_success(
            "POST",
            "/api/content",
            token=user["token"],
            json_body={
                "title": title,
                "body": body,
                "content_type": content_type,
                "visibility": visibility,
                "tag_ids": tag_ids or [10],
                "work_ids": work_ids or [],
                "character_ids": character_ids or [],
            },
        )
        if not isinstance(data, dict) or not isinstance(data.get("content_id"), int):
            raise AssertionError("POST /api/content returned unexpected payload")
        return int(data["content_id"])

    @classmethod
    def public_content_id(cls) -> int:
        return cls.db.get_public_content_id()

    @classmethod
    def public_work_id(cls) -> int:
        return cls.db.get_public_work_id()

    def expect_success(self, client: ApiClient, method: str, path: str, **kwargs):
        return client.expect_success(method, path, **kwargs)

    def expect_error(self, client: ApiClient, method: str, path: str, **kwargs):
        return client.expect_error(method, path, **kwargs)
