from __future__ import annotations

from datetime import datetime, timedelta

from tests.integration.base import LiveBackendTestCase


class AuthorizationOwnerTests(LiveBackendTestCase):
    def _create_owner_asset(self, owner_user: dict, *, label: str) -> int:
        return self.db.create_asset(owner_user["user_id"], f"{label}_{owner_user['user_id']}")

    def _submit_request(self, requester_user: dict, asset_id: int, *, message: str) -> int:
        self.expect_success(
            requester_user["client"],
            "POST",
            "/api/auth/request",
            json_body={"asset_id": asset_id, "message": message},
        )
        row = self.db.find_request(asset_id, requester_user["user_id"])
        self.assertIsNotNone(row)
        return int(row["request_id"])

    def test_owner_can_reject_pending_request(self):
        owner_user = self.register_temp_user("owner")
        requester_user = self.register_temp_user("requester")
        asset_id = self._create_owner_asset(owner_user, label="reject_asset")

        request_id = self._submit_request(requester_user, asset_id, message="integration reject flow")

        pending = self.expect_success(owner_user["client"], "GET", "/api/auth/pending")
        self.assertIsInstance(pending, list)
        self.assertTrue(any(item["request_id"] == request_id for item in pending))

        self.expect_success(
            owner_user["client"],
            "POST",
            f"/api/auth/resolve/{request_id}",
            json_body={"decision": "rejected"},
        )

        row = self.db.find_request(asset_id, requester_user["user_id"])
        self.assertIsNotNone(row)
        self.assertEqual(row["request_status"], "rejected")
        self.assertEqual(row["resolved_by"], owner_user["user_id"])

    def test_owner_can_approve_then_revoke_authorization(self):
        owner_user = self.register_temp_user("owner")
        requester_user = self.register_temp_user("requester")
        asset_id = self._create_owner_asset(owner_user, label="approve_asset")

        request_id = self._submit_request(requester_user, asset_id, message="integration approve flow")
        valid_until = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

        self.expect_success(
            owner_user["client"],
            "POST",
            f"/api/auth/resolve/{request_id}",
            json_body={"decision": "approved", "valid_until": valid_until},
        )

        authorization = self.db.find_authorization_by_request(request_id)
        self.assertIsNotNone(authorization)
        self.assertEqual(authorization["authorization_status"], "active")
        self.assertEqual(authorization["granted_by"], owner_user["user_id"])
        self.assertEqual(authorization["grantee_id"], requester_user["user_id"])

        my_assets = self.expect_success(requester_user["client"], "GET", "/api/auth/my-assets")
        self.assertIsInstance(my_assets, list)
        self.assertTrue(any(item["authorization_id"] == authorization["authorization_id"] for item in my_assets))

        self.expect_success(
            owner_user["client"],
            "POST",
            f"/api/auth/revoke/{authorization['authorization_id']}",
        )

        authorization = self.db.find_authorization_by_request(request_id)
        self.assertIsNotNone(authorization)
        self.assertEqual(authorization["authorization_status"], "revoked")

        my_assets = self.expect_success(requester_user["client"], "GET", "/api/auth/my-assets")
        self.assertIsInstance(my_assets, list)
        self.assertFalse(any(item["authorization_id"] == authorization["authorization_id"] for item in my_assets))
