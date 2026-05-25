from __future__ import annotations

from tests.integration.base import LiveBackendTestCase


class WorkDetailTests(LiveBackendTestCase):
    def test_work_detail_returns_work_characters_and_contents(self):
        work_id = self.public_work_id()
        data = self.api.expect_success("GET", f"/api/works/{work_id}")
        self.assertIsInstance(data, dict)
        self.assertEqual(data["work_id"], work_id)
        self.assertIn("characters", data)
        self.assertIn("contents", data)
        self.assertIsInstance(data["characters"], list)
        self.assertIsInstance(data["contents"], dict)
        self.assertIn("items", data["contents"])
        self.assertIsInstance(data["contents"]["items"], list)

    def test_work_detail_returns_404_for_missing_work(self):
        self.api.expect_error("GET", "/api/works/999999", expected_status=404)
