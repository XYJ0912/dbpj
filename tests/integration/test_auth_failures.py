from __future__ import annotations

from datetime import datetime, timedelta

from tests.integration.base import LiveBackendTestCase


class AuthFailureTests(LiveBackendTestCase):
    def test_login_required_endpoints_return_401_without_token(self):
        cases = [
            ("GET", "/api/user/me", None),
            ("GET", "/api/auth/overview", None),
            ("GET", "/api/admin/stats", None),
            (
                "POST",
                "/api/content",
                {"title": "no token", "body": "x", "content_type": "text", "visibility": "public", "tag_ids": [10]},
            ),
        ]
        for method, path, json_body in cases:
            with self.subTest(method=method, path=path):
                self.api.expect_error(
                    method,
                    path,
                    json_body=json_body,
                    expected_status=401,
                    expected_code=401,
                )

    def test_plain_user_cannot_access_admin_or_other_feed(self):
        plain_user = self.register_temp_user("plain")
        other_user = self.register_temp_user("other")

        self.expect_error(plain_user["client"], "GET", "/api/admin/stats", expected_status=403)
        self.expect_error(
            plain_user["client"],
            "GET",
            f"/api/user/{other_user['user_id']}/feed",
            expected_status=403,
        )
        self.expect_error(
            plain_user["client"],
            "POST",
            f"/api/admin/user/{other_user['user_id']}/deactivate",
            params={"mode": "suspended"},
            expected_status=403,
        )

    def test_non_owner_cannot_resolve_or_revoke_authorization(self):
        owner = self.register_temp_user("owner")
        requester = self.register_temp_user("requester")
        outsider = self.register_temp_user("outsider")

        asset_id = self.db.create_asset(owner["user_id"], f"auth_fail_{owner['user_id']}")
        self.expect_success(
            requester["client"],
            "POST",
            "/api/auth/request",
            json_body={"asset_id": asset_id, "message": "please authorize"},
        )
        request_row = self.db.find_request(asset_id, requester["user_id"])
        self.assertIsNotNone(request_row)
        request_id = int(request_row["request_id"])

        self.expect_error(
            outsider["client"],
            "POST",
            f"/api/auth/resolve/{request_id}",
            json_body={"decision": "rejected"},
        )

        valid_until = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        self.expect_success(
            owner["client"],
            "POST",
            f"/api/auth/resolve/{request_id}",
            json_body={"decision": "approved", "valid_until": valid_until},
        )
        authorization = self.db.find_authorization_by_request(request_id)
        self.assertIsNotNone(authorization)

        self.expect_error(
            outsider["client"],
            "POST",
            f"/api/auth/revoke/{authorization['authorization_id']}",
        )
