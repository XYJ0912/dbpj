from __future__ import annotations

from tests.integration.base import LiveBackendTestCase


class ContentVisibilityTests(LiveBackendTestCase):
    def test_visibility_matrix_for_followers_private_and_draft(self):
        author = self.register_temp_user("author")
        follower = self.register_temp_user("follower")
        stranger = self.register_temp_user("stranger")
        self.db.create_follow(follower["user_id"], author["user_id"])

        followers_only_id = self.publish_content(
            author,
            title="followers only post",
            visibility="followers_only",
        )
        private_id = self.publish_content(
            author,
            title="private post",
            visibility="private",
        )
        draft_id = self.db.create_draft_content(author["user_id"], "draft post")

        author_detail = self.expect_success(author["client"], "GET", f"/api/content/{followers_only_id}")
        follower_detail = self.expect_success(follower["client"], "GET", f"/api/content/{followers_only_id}")
        self.assertEqual(author_detail["content_id"], followers_only_id)
        self.assertEqual(follower_detail["content_id"], followers_only_id)
        self.expect_error(stranger["client"], "GET", f"/api/content/{followers_only_id}", expected_status=404)

        owner_private = self.expect_success(author["client"], "GET", f"/api/content/{private_id}")
        self.assertEqual(owner_private["content_id"], private_id)
        self.expect_error(follower["client"], "GET", f"/api/content/{private_id}", expected_status=404)
        self.expect_error(stranger["client"], "GET", f"/api/content/{private_id}", expected_status=404)

        owner_draft = self.expect_success(author["client"], "GET", f"/api/content/{draft_id}")
        self.assertEqual(owner_draft["content_id"], draft_id)
        self.expect_error(follower["client"], "GET", f"/api/content/{draft_id}", expected_status=404)
        self.expect_error(stranger["client"], "GET", f"/api/content/{draft_id}", expected_status=404)
        self.expect_error(author["client"], "GET", f"/api/content/{draft_id}/comments", expected_status=404)
