from __future__ import annotations

import time
from datetime import datetime, timedelta

from tests.integration.base import LiveBackendTestCase


class DatabaseProcedureRegressionTests(LiveBackendTestCase):
    def test_save_homepage_conflict_detected(self):
        user = self.register_temp_user("homepage")
        homepage = self.expect_success(user["client"], "GET", f"/api/homepage/{user['user_id']}")
        self.assertIsInstance(homepage, dict)
        stale_updated_at = homepage["updated_at"]

        time.sleep(1.1)

        self.expect_success(
            user["client"],
            "PUT",
            "/api/homepage",
            json_body={
                "homepage_config": {
                    "template": {"name": "default_two_column", "slot_count": 6},
                    "theme": "first-save",
                    "background_url": "/assets/test/first.png",
                    "layout": [],
                },
                "last_read_updated_at": stale_updated_at,
            },
        )

        self.expect_error(
            user["client"],
            "PUT",
            "/api/homepage",
            json_body={
                "homepage_config": {
                    "template": {"name": "default_two_column", "slot_count": 6},
                    "theme": "stale-save",
                    "background_url": "/assets/test/stale.png",
                    "layout": [],
                },
                "last_read_updated_at": stale_updated_at,
            },
        )

    def test_content_moderator_can_archive_other_users_content(self):
        author = self.register_temp_user("author")
        moderator = self.register_temp_user("moderator", roles=("content_moderator",))
        content_id = self.publish_content(author, title="moderated archive target")

        self.expect_success(moderator["client"], "PUT", f"/api/content/{content_id}/archive")
        self.assertEqual(self.db.get_content_status(content_id), "archived")

    def test_admin_deactivated_branch_converges_related_records(self):
        admin = self.register_temp_user("admin", roles=("admin",))
        target = self.register_temp_user("target")
        requester = self.register_temp_user("requester")

        content_id = self.publish_content(target, title="deactivate target content")
        asset_id = self.db.create_asset(target["user_id"], f"deactivate_asset_{target['user_id']}")

        self.expect_success(
            requester["client"],
            "POST",
            "/api/auth/request",
            json_body={"asset_id": asset_id, "message": "temporary authorization"},
        )
        request_row = self.db.find_request(asset_id, requester["user_id"])
        self.assertIsNotNone(request_row)
        request_id = int(request_row["request_id"])
        valid_until = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")

        self.expect_success(
            target["client"],
            "POST",
            f"/api/auth/resolve/{request_id}",
            json_body={"decision": "approved", "valid_until": valid_until},
        )
        authorization = self.db.find_authorization_by_request(request_id)
        self.assertIsNotNone(authorization)

        self.expect_success(
            admin["client"],
            "POST",
            f"/api/admin/user/{target['user_id']}/deactivate",
            params={"mode": "deactivated"},
        )

        self.assertEqual(self.db.get_user_status(target["user_id"]), "deactivated")
        self.assertEqual(self.db.get_content_status(content_id), "archived")
        self.assertEqual(self.db.get_asset_status(asset_id), "disabled")
        self.assertEqual(
            self.db.get_authorization_status(int(authorization["authorization_id"])),
            "revoked",
        )
