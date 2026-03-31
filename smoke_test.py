from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from tests.helpers.api_client import ApiClient
from tests.helpers.db_helper import DBHelper


DEFAULT_BASE_URL = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:5000")


@dataclass
class CheckResult:
    name: str
    status: str
    http_status: Optional[int] = None
    detail: str = ""


class SmokeTestError(RuntimeError):
    pass


class BackendSmokeTester:
    def __init__(self, base_url: str, *, keep_data: bool = False):
        self.base_url = base_url.rstrip("/")
        self.keep_data = keep_data
        self.api = ApiClient(self.base_url)
        self.db = DBHelper()
        self.results: list[CheckResult] = []

        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.user_id: Optional[int] = None
        self.token: Optional[str] = None

        self.public_content_id: Optional[int] = None
        self.public_tag_id: Optional[int] = None
        self.public_work_id: Optional[int] = None
        self.public_character_id: Optional[int] = None

        self.created_content_id: Optional[int] = None
        self.created_content_id_for_delete: Optional[int] = None
        self.authorization_request_submitted = False

        self.cleanup_user_ids: list[int] = []

    def log(self, name: str, ok: bool, http_status: Optional[int] = None, detail: str = ""):
        status = "PASS" if ok else "FAIL"
        self.results.append(CheckResult(name=name, status=status, http_status=http_status, detail=detail))
        print(f"[{status}] {name}")
        if http_status is not None:
            print(f"       status={http_status}")
        if detail:
            print(f"       detail={detail}")

    def skip(self, name: str, detail: str):
        self.results.append(CheckResult(name=name, status="SKIP", detail=detail))
        print(f"[SKIP] {name}")
        print(f"       detail={detail}")

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        auth: bool = False,
        token: Optional[str] = None,
    ):
        bearer = token
        if auth and bearer is None:
            if not self.token:
                raise SmokeTestError(f"Missing token for authenticated request: {method} {path}")
            bearer = self.token
        result = self.api.request(method, path, json_body=json_body, params=params, token=bearer)
        return result.response, result.body

    def _short_body(self, body: Any, limit: int = 260) -> str:
        return self.api.short_body(body, limit)

    def _assert_json(self, name: str, response, body: Any) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise SmokeTestError(f"{name} returned non-JSON body: {self._short_body(body)}")
        return body

    def _assert_success_envelope(
        self,
        name: str,
        response,
        body: Any,
        *,
        expected_statuses: set[int] | None = None,
        data_validator: Optional[Callable[[Any], tuple[bool, str]]] = None,
    ) -> Any:
        payload = self._assert_json(name, response, body)
        if expected_statuses is None:
            expected_statuses = {200}
        if response.status_code not in expected_statuses:
            raise SmokeTestError(f"{name} returned {response.status_code}: {self._short_body(payload)}")
        if payload.get("code") != 0:
            raise SmokeTestError(f"{name} business error: {self._short_body(payload)}")
        data = payload.get("data")
        if data_validator:
            ok, reason = data_validator(data)
            if not ok:
                raise SmokeTestError(f"{name} payload mismatch: {reason}")
        return data

    def _assert_plain_json(
        self,
        name: str,
        response,
        body: Any,
        *,
        expected_statuses: set[int] | None = None,
        validator: Optional[Callable[[dict[str, Any]], tuple[bool, str]]] = None,
    ) -> dict[str, Any]:
        payload = self._assert_json(name, response, body)
        if expected_statuses is None:
            expected_statuses = {200}
        if response.status_code not in expected_statuses:
            raise SmokeTestError(f"{name} returned {response.status_code}: {self._short_body(payload)}")
        if validator:
            ok, reason = validator(payload)
            if not ok:
                raise SmokeTestError(f"{name} payload mismatch: {reason}")
        return payload

    def _record_http_run(self, name: str, fn: Callable[[], tuple[int, str]]):
        try:
            http_status, detail = fn()
            self.log(name, True, http_status=http_status, detail=detail)
        except SmokeTestError as exc:
            self.log(name, False, detail=str(exc))

    def _register_temp_user(self, prefix: str) -> dict[str, Any]:
        suffix = f"{int(time.time() * 1000)}_{len(self.cleanup_user_ids)}"
        username = f"{prefix}_{suffix}"
        password = "123456"
        data = self.api.register_user(username, password, email=f"{username}@example.com")
        user_id = int(data["user_id"])
        self.cleanup_user_ids.append(user_id)
        return {
            "user_id": user_id,
            "username": username,
            "password": password,
            "token": data["token"],
        }

    def preflight(self):
        def check_root() -> tuple[int, str]:
            response, body = self._request("GET", "/")
            payload = self._assert_plain_json(
                "GET /",
                response,
                body,
                validator=lambda x: (
                    x.get("status") == "running" and isinstance(x.get("name"), str),
                    "expected status=running and name field",
                ),
            )
            return response.status_code, f"service={payload.get('name')}"

        def check_api_index() -> tuple[int, str]:
            response, body = self._request("GET", "/api")
            payload = self._assert_plain_json(
                "GET /api",
                response,
                body,
                validator=lambda x: (
                    isinstance(x.get("routes"), list) and isinstance(x.get("total"), int),
                    "expected routes list and total integer",
                ),
            )
            return response.status_code, f"routes={payload['total']}"

        self._record_http_run("GET /", check_root)
        self._record_http_run("GET /api", check_api_index)
    def test_public_catalog(self):
        def get_hot() -> tuple[int, str]:
            response, body = self._request("GET", "/api/content/hot")
            data = self._assert_success_envelope("GET /api/content/hot", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("GET /api/content/hot payload mismatch: missing items list")
            if items:
                self.public_content_id = items[0]["content_id"]
            return response.status_code, f"items={len(items)} public_content_id={self.public_content_id}"

        def get_top_liked() -> tuple[int, str]:
            response, body = self._request("GET", "/api/content/top-liked")
            data = self._assert_success_envelope("GET /api/content/top-liked", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("GET /api/content/top-liked payload mismatch: missing items list")
            return response.status_code, f"items={len(items)}"

        def get_top_favorited() -> tuple[int, str]:
            response, body = self._request("GET", "/api/content/top-favorited")
            data = self._assert_success_envelope("GET /api/content/top-favorited", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("GET /api/content/top-favorited payload mismatch: missing items list")
            return response.status_code, f"items={len(items)}"

        def get_tags() -> tuple[int, str]:
            response, body = self._request("GET", "/api/tags")
            data = self._assert_success_envelope("GET /api/tags", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("GET /api/tags payload mismatch: expected list")
            if data:
                self.public_tag_id = data[0]["tag_id"]
            return response.status_code, f"items={len(data)} tag_id={self.public_tag_id}"

        def get_works() -> tuple[int, str]:
            response, body = self._request("GET", "/api/works")
            data = self._assert_success_envelope("GET /api/works", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("GET /api/works payload mismatch: missing items list")
            if items:
                self.public_work_id = items[0]["work_id"]
            return response.status_code, f"items={len(items)} work_id={self.public_work_id}"

        def get_characters() -> tuple[int, str]:
            response, body = self._request("GET", "/api/characters")
            data = self._assert_success_envelope("GET /api/characters", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("GET /api/characters payload mismatch: missing items list")
            if items:
                self.public_character_id = items[0]["character_id"]
            return response.status_code, f"items={len(items)} character_id={self.public_character_id}"

        def get_by_tag() -> tuple[int, str]:
            if not self.public_tag_id:
                raise SmokeTestError("GET /api/content/by-tag skipped: no tag_id discovered")
            response, body = self._request("GET", "/api/content/by-tag", params={"tag_id": self.public_tag_id})
            data = self._assert_success_envelope("GET /api/content/by-tag", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("GET /api/content/by-tag payload mismatch: missing items list")
            return response.status_code, f"tag_id={self.public_tag_id} items={len(items)}"

        def get_by_work() -> tuple[int, str]:
            if not self.public_work_id:
                raise SmokeTestError("GET /api/content/by-work skipped: no work_id discovered")
            response, body = self._request("GET", "/api/content/by-work", params={"work_id": self.public_work_id})
            data = self._assert_success_envelope("GET /api/content/by-work", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("GET /api/content/by-work payload mismatch: missing items list")
            return response.status_code, f"work_id={self.public_work_id} items={len(items)}"

        self._record_http_run("GET /api/content/hot", get_hot)
        self._record_http_run("GET /api/content/top-liked", get_top_liked)
        self._record_http_run("GET /api/content/top-favorited", get_top_favorited)
        self._record_http_run("GET /api/tags", get_tags)
        self._record_http_run("GET /api/works", get_works)
        self._record_http_run("GET /api/characters", get_characters)

        if self.public_tag_id:
            self._record_http_run("GET /api/content/by-tag", get_by_tag)
        else:
            self.skip("GET /api/content/by-tag", "no tag_id discovered from public catalog")

        if self.public_work_id:
            self._record_http_run("GET /api/content/by-work", get_by_work)
        else:
            self.skip("GET /api/content/by-work", "no work_id discovered from public catalog")

    def register_and_login(self):
        user = self._register_temp_user("smoke")
        self.username = user["username"]
        self.password = user["password"]
        self.user_id = user["user_id"]
        self.token = user["token"]

        def register() -> tuple[int, str]:
            return 200, f"user_id={self.user_id}"

        def login() -> tuple[int, str]:
            data = self.api.login_user(self.username, self.password)
            token = data.get("token")
            if not isinstance(token, str) or not token:
                raise SmokeTestError("POST /api/user/login payload mismatch: missing token")
            self.token = token
            return 200, f"user_id={data.get('user_id')}"

        self._record_http_run("POST /api/user/register", register)
        self._record_http_run("POST /api/user/login", login)

    def test_user_endpoints(self):
        if not self.user_id:
            self.skip("Authenticated user endpoints", "registration did not complete")
            return

        def get_me() -> tuple[int, str]:
            response, body = self._request("GET", "/api/user/me", auth=True)
            data = self._assert_success_envelope("GET /api/user/me", response, body)
            if not isinstance(data, dict) or data.get("user_id") != self.user_id:
                raise SmokeTestError("GET /api/user/me payload mismatch: wrong user_id")
            return response.status_code, f"user_id={data['user_id']}"

        def get_profile() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/user/{self.user_id}/profile")
            data = self._assert_success_envelope(f"GET /api/user/{self.user_id}/profile", response, body)
            if not isinstance(data, dict) or data.get("user_id") != self.user_id:
                raise SmokeTestError("profile payload mismatch")
            return response.status_code, f"username={data.get('username')}"

        def get_behavior() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/user/{self.user_id}/behavior")
            data = self._assert_success_envelope(f"GET /api/user/{self.user_id}/behavior", response, body)
            if not isinstance(data, dict) or data.get("user_id") != self.user_id:
                raise SmokeTestError("behavior payload mismatch")
            return response.status_code, "behavior loaded"

        def get_tags() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/user/{self.user_id}/tags")
            data = self._assert_success_envelope(f"GET /api/user/{self.user_id}/tags", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("tag preference payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def get_works() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/user/{self.user_id}/works")
            data = self._assert_success_envelope(f"GET /api/user/{self.user_id}/works", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("work preference payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def get_friends() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/user/{self.user_id}/friends")
            data = self._assert_success_envelope(f"GET /api/user/{self.user_id}/friends", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("friends payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def get_feed() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/user/{self.user_id}/feed", auth=True)
            data = self._assert_success_envelope(f"GET /api/user/{self.user_id}/feed", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("feed payload mismatch: missing items list")
            return response.status_code, f"items={len(items)}"

        self._record_http_run("GET /api/user/me", get_me)
        self._record_http_run(f"GET /api/user/{self.user_id}/profile", get_profile)
        self._record_http_run(f"GET /api/user/{self.user_id}/behavior", get_behavior)
        self._record_http_run(f"GET /api/user/{self.user_id}/tags", get_tags)
        self._record_http_run(f"GET /api/user/{self.user_id}/works", get_works)
        self._record_http_run(f"GET /api/user/{self.user_id}/friends", get_friends)
        self._record_http_run(f"GET /api/user/{self.user_id}/feed", get_feed)

    def test_social(self):
        if not self.user_id:
            self.skip("Social endpoints", "registration did not complete")
            return

        target_id = 2

        def follow() -> tuple[int, str]:
            response, body = self._request("POST", f"/api/follow/{target_id}", auth=True)
            self._assert_success_envelope(f"POST /api/follow/{target_id}", response, body)
            return response.status_code, f"target_id={target_id}"

        def feed_after_follow() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/user/{self.user_id}/feed", auth=True)
            data = self._assert_success_envelope(f"GET /api/user/{self.user_id}/feed (after follow)", response, body)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SmokeTestError("feed payload mismatch after follow")
            return response.status_code, f"items={len(items)}"

        def unfollow() -> tuple[int, str]:
            response, body = self._request("DELETE", f"/api/follow/{target_id}", auth=True)
            self._assert_success_envelope(f"DELETE /api/follow/{target_id}", response, body)
            return response.status_code, f"target_id={target_id}"

        self._record_http_run(f"POST /api/follow/{target_id}", follow)
        self._record_http_run(f"GET /api/user/{self.user_id}/feed (after follow)", feed_after_follow)
        self._record_http_run(f"DELETE /api/follow/{target_id}", unfollow)

    def test_homepage(self):
        if not self.user_id:
            self.skip("Homepage endpoints", "registration did not complete")
            return

        def list_templates() -> tuple[int, str]:
            response, body = self._request("GET", "/api/homepage/templates")
            data = self._assert_success_envelope("GET /api/homepage/templates", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("templates payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def get_homepage() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/homepage/{self.user_id}", auth=True)
            data = self._assert_success_envelope(f"GET /api/homepage/{self.user_id}", response, body)
            if not isinstance(data, dict) or data.get("user_id") != self.user_id:
                raise SmokeTestError("homepage payload mismatch")
            return response.status_code, f"homepage_id={data.get('homepage_id')}"

        def save_homepage() -> tuple[int, str]:
            response, body = self._request(
                "PUT",
                "/api/homepage",
                auth=True,
                json_body={
                    "theme": "smoke-test",
                    "background_url": "/assets/test/bg.png",
                    "homepage_config": {
                        "template": {"name": "default_two_column", "slot_count": 6},
                        "theme": "smoke-test",
                        "background_url": "/assets/test/bg.png",
                        "layout": [
                            {
                                "component_id": "smoke_component",
                                "component_type": "recent_content",
                                "position": {"x": 0, "y": 0, "w": 12, "h": 4},
                                "z_index": 1,
                                "title": "Smoke Test",
                                "config": {"content_ids": [], "limit": 1},
                            }
                        ],
                    },
                },
            )
            self._assert_success_envelope("PUT /api/homepage", response, body)
            return response.status_code, "homepage saved"

        self._record_http_run("GET /api/homepage/templates", list_templates)
        self._record_http_run(f"GET /api/homepage/{self.user_id}", get_homepage)
        self._record_http_run("PUT /api/homepage", save_homepage)
    def test_authorization(self):
        if not self.user_id:
            self.skip("Authorization endpoints", "registration did not complete")
            return

        def overview() -> tuple[int, str]:
            response, body = self._request("GET", "/api/auth/overview", auth=True)
            data = self._assert_success_envelope("GET /api/auth/overview", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("overview payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def my_assets() -> tuple[int, str]:
            response, body = self._request("GET", "/api/auth/my-assets", auth=True)
            data = self._assert_success_envelope("GET /api/auth/my-assets", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("my-assets payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def active_usage() -> tuple[int, str]:
            response, body = self._request("GET", "/api/auth/active-usage", auth=True)
            data = self._assert_success_envelope("GET /api/auth/active-usage", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("active-usage payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def pending() -> tuple[int, str]:
            response, body = self._request("GET", "/api/auth/pending", auth=True)
            data = self._assert_success_envelope("GET /api/auth/pending", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("pending payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def submit_request() -> tuple[int, str]:
            response, body = self._request(
                "POST",
                "/api/auth/request",
                auth=True,
                json_body={"asset_id": 1, "message": "smoke test request"},
            )
            self._assert_success_envelope("POST /api/auth/request", response, body)
            self.authorization_request_submitted = True
            return response.status_code, "asset_id=1"

        self._record_http_run("GET /api/auth/overview", overview)
        self._record_http_run("GET /api/auth/my-assets", my_assets)
        self._record_http_run("GET /api/auth/active-usage", active_usage)
        self._record_http_run("GET /api/auth/pending", pending)
        self._record_http_run("POST /api/auth/request", submit_request)

    def test_privileged_authorization(self):
        owner_user = self._register_temp_user("owner")
        requester_user = self._register_temp_user("requester")
        reject_asset_id = self.db.create_asset(owner_user["user_id"], f"reject_asset_{owner_user['user_id']}")
        approve_asset_id = self.db.create_asset(owner_user["user_id"], f"approve_asset_{owner_user['user_id']}")

        def resolve_request() -> tuple[int, str]:
            self.api.expect_success(
                "POST",
                "/api/auth/request",
                json_body={"asset_id": reject_asset_id, "message": "smoke reject request"},
                token=requester_user["token"],
            )
            request_row = self.db.find_request(reject_asset_id, requester_user["user_id"])
            if not request_row:
                raise SmokeTestError("failed to locate pending request for resolve flow")
            request_id = int(request_row["request_id"])

            response, body = self._request("GET", "/api/auth/pending", token=owner_user["token"])
            data = self._assert_success_envelope("GET /api/auth/pending (owner)", response, body)
            if not isinstance(data, list) or not any(item["request_id"] == request_id for item in data):
                raise SmokeTestError("owner pending list does not include the temporary request")

            response, body = self._request(
                "POST",
                f"/api/auth/resolve/{request_id}",
                token=owner_user["token"],
                json_body={"decision": "rejected"},
            )
            self._assert_success_envelope(f"POST /api/auth/resolve/{request_id}", response, body)

            request_row = self.db.find_request(reject_asset_id, requester_user["user_id"])
            if not request_row or request_row["request_status"] != "rejected":
                raise SmokeTestError("request was not marked rejected")
            return response.status_code, f"request_id={request_id} rejected"

        def revoke_authorization() -> tuple[int, str]:
            self.api.expect_success(
                "POST",
                "/api/auth/request",
                json_body={"asset_id": approve_asset_id, "message": "smoke approve request"},
                token=requester_user["token"],
            )
            request_row = self.db.find_request(approve_asset_id, requester_user["user_id"])
            if not request_row:
                raise SmokeTestError("failed to locate pending request for revoke flow")
            request_id = int(request_row["request_id"])
            valid_until = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

            response, body = self._request(
                "POST",
                f"/api/auth/resolve/{request_id}",
                token=owner_user["token"],
                json_body={"decision": "approved", "valid_until": valid_until},
            )
            self._assert_success_envelope(f"POST /api/auth/resolve/{request_id} approve", response, body)

            authorization = self.db.find_authorization_by_request(request_id)
            if not authorization or authorization["authorization_status"] != "active":
                raise SmokeTestError("authorization was not created as active")

            response, body = self._request("GET", "/api/auth/my-assets", token=requester_user["token"])
            data = self._assert_success_envelope("GET /api/auth/my-assets (grantee)", response, body)
            if not isinstance(data, list) or not any(
                item["authorization_id"] == authorization["authorization_id"] for item in data
            ):
                raise SmokeTestError("approved authorization not visible to grantee")

            response, body = self._request(
                "POST",
                f"/api/auth/revoke/{authorization['authorization_id']}",
                token=owner_user["token"],
            )
            self._assert_success_envelope(
                f"POST /api/auth/revoke/{authorization['authorization_id']}",
                response,
                body,
            )

            authorization = self.db.find_authorization_by_request(request_id)
            if not authorization or authorization["authorization_status"] != "revoked":
                raise SmokeTestError("authorization was not revoked")
            return response.status_code, f"authorization_id={authorization['authorization_id']} revoked"

        self._record_http_run("POST /api/auth/resolve/<id>", resolve_request)
        self._record_http_run("POST /api/auth/revoke/<id>", revoke_authorization)

    def publish_content(self, title_suffix: str) -> int:
        tag_ids = [self.public_tag_id] if self.public_tag_id else [10]
        work_ids = [self.public_work_id] if self.public_work_id else []

        response, body = self._request(
            "POST",
            "/api/content",
            auth=True,
            json_body={
                "title": f"Smoke Test Content {title_suffix}",
                "body": "Created by smoke_test.py",
                "content_type": "text",
                "visibility": "public",
                "tag_ids": tag_ids,
                "work_ids": work_ids,
            },
        )
        data = self._assert_success_envelope("POST /api/content", response, body)
        if not isinstance(data, dict) or not isinstance(data.get("content_id"), int):
            raise SmokeTestError("POST /api/content payload mismatch: missing content_id")
        return data["content_id"]

    def test_content(self):
        if not self.user_id:
            self.skip("Content endpoints", "registration did not complete")
            return
        if not self.public_content_id:
            self.skip("Content endpoints", "public catalog did not discover a content_id")
            return

        def detail_public() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/content/{self.public_content_id}", auth=True)
            data = self._assert_success_envelope(f"GET /api/content/{self.public_content_id}", response, body)
            if not isinstance(data, dict) or data.get("content_id") != self.public_content_id:
                raise SmokeTestError("content detail payload mismatch")
            return response.status_code, f"content_id={self.public_content_id}"

        def comments_public() -> tuple[int, str]:
            response, body = self._request("GET", f"/api/content/{self.public_content_id}/comments", auth=True)
            data = self._assert_success_envelope(f"GET /api/content/{self.public_content_id}/comments", response, body)
            if not isinstance(data, list):
                raise SmokeTestError("comments payload mismatch: expected list")
            return response.status_code, f"items={len(data)}"

        def browse_public() -> tuple[int, str]:
            response, body = self._request(
                "POST",
                f"/api/content/{self.public_content_id}/browse",
                auth=True,
                json_body={"duration_seconds": 15},
            )
            self._assert_success_envelope(f"POST /api/content/{self.public_content_id}/browse", response, body)
            return response.status_code, f"content_id={self.public_content_id}"

        def like_public() -> tuple[int, str]:
            response, body = self._request("POST", f"/api/content/{self.public_content_id}/like", auth=True)
            self._assert_success_envelope(f"POST /api/content/{self.public_content_id}/like", response, body)
            return response.status_code, f"content_id={self.public_content_id}"

        def unlike_public() -> tuple[int, str]:
            response, body = self._request("DELETE", f"/api/content/{self.public_content_id}/like", auth=True)
            self._assert_success_envelope(f"DELETE /api/content/{self.public_content_id}/like", response, body)
            return response.status_code, f"content_id={self.public_content_id}"

        def favorite_public() -> tuple[int, str]:
            response, body = self._request("POST", f"/api/content/{self.public_content_id}/favorite", auth=True)
            self._assert_success_envelope(f"POST /api/content/{self.public_content_id}/favorite", response, body)
            return response.status_code, f"content_id={self.public_content_id}"

        def unfavorite_public() -> tuple[int, str]:
            response, body = self._request("DELETE", f"/api/content/{self.public_content_id}/favorite", auth=True)
            self._assert_success_envelope(f"DELETE /api/content/{self.public_content_id}/favorite", response, body)
            return response.status_code, f"content_id={self.public_content_id}"
        def publish_first() -> tuple[int, str]:
            self.created_content_id = self.publish_content("A")
            return 200, f"content_id={self.created_content_id}"

        def detail_created() -> tuple[int, str]:
            if not self.created_content_id:
                raise SmokeTestError("created content missing")
            response, body = self._request("GET", f"/api/content/{self.created_content_id}", auth=True)
            data = self._assert_success_envelope(f"GET /api/content/{self.created_content_id}", response, body)
            if not isinstance(data, dict) or data.get("content_id") != self.created_content_id:
                raise SmokeTestError("created content detail payload mismatch")
            return response.status_code, f"content_id={self.created_content_id}"

        def comment_created() -> tuple[int, str]:
            if not self.created_content_id:
                raise SmokeTestError("created content missing")
            response, body = self._request(
                "POST",
                f"/api/content/{self.created_content_id}/comment",
                auth=True,
                json_body={"text": "Smoke test comment"},
            )
            self._assert_success_envelope(f"POST /api/content/{self.created_content_id}/comment", response, body)
            return response.status_code, f"content_id={self.created_content_id}"

        def archive_created() -> tuple[int, str]:
            if not self.created_content_id:
                raise SmokeTestError("created content missing")
            response, body = self._request("PUT", f"/api/content/{self.created_content_id}/archive", auth=True)
            self._assert_success_envelope(f"PUT /api/content/{self.created_content_id}/archive", response, body)
            return response.status_code, f"content_id={self.created_content_id}"

        def publish_second() -> tuple[int, str]:
            self.created_content_id_for_delete = self.publish_content("B")
            return 200, f"content_id={self.created_content_id_for_delete}"

        def delete_second() -> tuple[int, str]:
            if not self.created_content_id_for_delete:
                raise SmokeTestError("delete target content missing")
            response, body = self._request("DELETE", f"/api/content/{self.created_content_id_for_delete}", auth=True)
            self._assert_success_envelope(
                f"DELETE /api/content/{self.created_content_id_for_delete}",
                response,
                body,
            )
            return response.status_code, f"content_id={self.created_content_id_for_delete}"

        self._record_http_run(f"GET /api/content/{self.public_content_id}", detail_public)
        self._record_http_run(f"GET /api/content/{self.public_content_id}/comments", comments_public)
        self._record_http_run(f"POST /api/content/{self.public_content_id}/browse", browse_public)
        self._record_http_run(f"POST /api/content/{self.public_content_id}/like", like_public)
        self._record_http_run(f"DELETE /api/content/{self.public_content_id}/like", unlike_public)
        self._record_http_run(f"POST /api/content/{self.public_content_id}/favorite", favorite_public)
        self._record_http_run(f"DELETE /api/content/{self.public_content_id}/favorite", unfavorite_public)
        self._record_http_run("POST /api/content", publish_first)
        self._record_http_run("GET /api/content/<created>", detail_created)
        self._record_http_run("POST /api/content/<created>/comment", comment_created)
        self._record_http_run("PUT /api/content/<created>/archive", archive_created)
        self._record_http_run("POST /api/content (second)", publish_second)
        self._record_http_run("DELETE /api/content/<created-second>", delete_second)

    def test_admin(self):
        admin_user = self._register_temp_user("admin")
        target_user = self._register_temp_user("target")
        self.db.grant_role(admin_user["user_id"], "admin")

        def admin_stats() -> tuple[int, str]:
            response, body = self._request("GET", "/api/admin/stats", token=admin_user["token"])
            data = self._assert_success_envelope("GET /api/admin/stats", response, body)
            if not isinstance(data, dict) or "users" not in data:
                raise SmokeTestError("admin stats payload mismatch")
            return response.status_code, f"users_total={data['users'].get('total')}"

        def deactivate_user() -> tuple[int, str]:
            response, body = self._request(
                "POST",
                f"/api/admin/user/{target_user['user_id']}/deactivate",
                token=admin_user["token"],
                params={"mode": "suspended"},
            )
            self._assert_success_envelope(
                f"POST /api/admin/user/{target_user['user_id']}/deactivate",
                response,
                body,
            )
            if self.db.get_user_status(target_user["user_id"]) != "suspended":
                raise SmokeTestError("target user status was not updated to suspended")
            login_response, login_body = self._request(
                "POST",
                "/api/user/login",
                json_body={"username": target_user["username"], "password": target_user["password"]},
            )
            payload = self._assert_json("POST /api/user/login after suspend", login_response, login_body)
            if login_response.status_code != 400 or payload.get("code") != 1:
                raise SmokeTestError("suspended user should not be able to log in")
            return response.status_code, f"target_user_id={target_user['user_id']} suspended"

        self._record_http_run("GET /api/admin/stats", admin_stats)
        self._record_http_run("POST /api/admin/user/<id>/deactivate", deactivate_user)

    def cleanup(self):
        if not self.keep_data:
            for user_id in reversed(self.cleanup_user_ids):
                try:
                    self.db.cleanup_user(user_id)
                except Exception as exc:
                    self.log("cleanup", False, detail=f"failed to cleanup user_id={user_id}: {exc}")
        self.db.close()

    def run(self):
        try:
            self.preflight()
            self.test_public_catalog()
            self.register_and_login()
            self.test_user_endpoints()
            self.test_social()
            self.test_homepage()
            self.test_authorization()
            self.test_content()
            self.test_privileged_authorization()
            self.test_admin()
        finally:
            self.cleanup()
        self.print_summary()

    def print_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")

        print("\n" + "=" * 60)
        print("Smoke Test Summary")
        print("=" * 60)
        print(f"Total:  {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped:{skipped}")

        if failed:
            print("\nFailed checks:")
            for result in self.results:
                if result.status == "FAIL":
                    line = f"- {result.name}"
                    if result.http_status is not None:
                        line += f" (status={result.http_status})"
                    print(line)
                    if result.detail:
                        print(f"  {result.detail}")

        if skipped:
            print("\nSkipped checks:")
            for result in self.results:
                if result.status == "SKIP":
                    print(f"- {result.name}")
                    print(f"  {result.detail}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test for the vertical_community backend API.")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Backend base URL. Default: {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--keep-data",
        action="store_true",
        help="Do not delete temporary smoke-test users and their related data after the run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tester = BackendSmokeTester(args.base_url, keep_data=args.keep_data)
    tester.run()
    return 1 if any(r.status == "FAIL" for r in tester.results) else 0


if __name__ == "__main__":
    sys.exit(main())

