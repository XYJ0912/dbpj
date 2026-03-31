from __future__ import annotations

from tests.integration.base import LiveBackendTestCase


class AdminEndpointTests(LiveBackendTestCase):
    def test_admin_stats_with_granted_role(self):
        admin_user = self.register_temp_user("admin")
        self.db.grant_role(admin_user["user_id"], "admin")

        data = self.expect_success(admin_user["client"], "GET", "/api/admin/stats")
        self.assertIsInstance(data, dict)
        self.assertIn("users", data)
        self.assertIn("contents", data)
        self.assertIn("interactions", data)
        self.assertIn("authorizations", data)

    def test_admin_can_suspend_temporary_user(self):
        admin_user = self.register_temp_user("admin")
        target_user = self.register_temp_user("target")
        self.db.grant_role(admin_user["user_id"], "admin")

        self.expect_success(
            admin_user["client"],
            "POST",
            f"/api/admin/user/{target_user['user_id']}/deactivate",
            params={"mode": "suspended"},
        )

        self.assertEqual(self.db.get_user_status(target_user["user_id"]), "suspended")

        result = self.api.request(
            "POST",
            "/api/user/login",
            json_body={"username": target_user["username"], "password": target_user["password"]},
        )
        self.assertEqual(result.response.status_code, 400)
        self.assertIsInstance(result.body, dict)
        self.assertEqual(result.body.get("code"), 1)
