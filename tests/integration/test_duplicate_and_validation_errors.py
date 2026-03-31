from __future__ import annotations

from tests.integration.base import LiveBackendTestCase


class ValidationAndDuplicateTests(LiveBackendTestCase):
    def test_register_and_login_validation_errors(self):
        self.api.expect_error(
            "POST",
            "/api/user/register",
            json_body={"username": "a", "email": "ok@example.com", "password": "123456"},
        )
        self.api.expect_error(
            "POST",
            "/api/user/register",
            json_body={"username": "validname", "email": "invalid-email", "password": "123456"},
        )
        self.api.expect_error(
            "POST",
            "/api/user/register",
            json_body={"username": "validname", "email": "ok@example.com", "password": "123"},
        )
        self.api.expect_error(
            "POST",
            "/api/user/login",
            json_body={"username": "", "password": ""},
        )

    def test_publish_and_comment_validation_errors(self):
        user = self.register_temp_user("validator")
        public_content_id = self.public_content_id()

        self.expect_error(
            user["client"],
            "POST",
            "/api/content",
            json_body={"title": "bad type", "body": "x", "content_type": "bad", "visibility": "public", "tag_ids": [10]},
        )
        self.expect_error(
            user["client"],
            "POST",
            "/api/content",
            json_body={"title": "bad visibility", "body": "x", "content_type": "text", "visibility": "friends", "tag_ids": [10]},
        )
        self.expect_error(
            user["client"],
            "POST",
            f"/api/content/{public_content_id}/comment",
            json_body={"text": "   "},
        )
        self.expect_error(
            user["client"],
            "POST",
            f"/api/content/{public_content_id}/comment",
            json_body={"text": "reply", "parent_comment_id": 999999},
        )

        self.expect_success(
            user["client"],
            "POST",
            f"/api/content/{public_content_id}/comment",
            json_body={"text": "top level"},
        )
        top_comment = self.db.find_latest_comment(user["user_id"], public_content_id)
        self.assertIsNotNone(top_comment)

        self.expect_success(
            user["client"],
            "POST",
            f"/api/content/{public_content_id}/comment",
            json_body={"text": "second level", "parent_comment_id": top_comment["comment_id"]},
        )
        second_comment = self.db.find_latest_comment(user["user_id"], public_content_id)
        self.assertIsNotNone(second_comment)
        self.assertNotEqual(second_comment["comment_id"], top_comment["comment_id"])

        self.expect_error(
            user["client"],
            "POST",
            f"/api/content/{public_content_id}/comment",
            json_body={"text": "third level", "parent_comment_id": second_comment["comment_id"]},
        )

    def test_duplicate_operations_return_business_errors(self):
        user = self.register_temp_user("dup")
        owner = self.register_temp_user("owner")
        public_content_id = self.public_content_id()
        asset_id = self.db.create_asset(owner["user_id"], f"dup_asset_{owner['user_id']}")

        self.expect_success(user["client"], "POST", "/api/follow/2")
        self.expect_error(user["client"], "POST", "/api/follow/2")

        self.expect_success(user["client"], "POST", f"/api/content/{public_content_id}/like")
        self.expect_error(user["client"], "POST", f"/api/content/{public_content_id}/like")

        self.expect_success(user["client"], "POST", f"/api/content/{public_content_id}/favorite")
        self.expect_error(user["client"], "POST", f"/api/content/{public_content_id}/favorite")

        self.expect_success(
            user["client"],
            "POST",
            "/api/auth/request",
            json_body={"asset_id": asset_id, "message": "first request"},
        )
        self.expect_error(
            user["client"],
            "POST",
            "/api/auth/request",
            json_body={"asset_id": asset_id, "message": "duplicate request"},
        )
