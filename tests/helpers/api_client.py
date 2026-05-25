from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

import requests


DEFAULT_BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5000")
REQUEST_TIMEOUT = 10


class ApiError(RuntimeError):
    pass


@dataclass
class ApiResponse:
    response: requests.Response
    body: Any


class ApiClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.session.trust_env = False

    def clone_with_token(self, token: str) -> "ApiClient":
        return ApiClient(self.base_url, token=token)

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        token: Optional[str] = None,
    ) -> ApiResponse:
        headers: dict[str, str] = {}
        bearer = token if token is not None else self.token
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"

        response = self.session.request(
            method=method,
            url=f"{self.base_url}{path}",
            json=json_body,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        return ApiResponse(response=response, body=body)

    @staticmethod
    def short_body(body: Any, limit: int = 260) -> str:
        if isinstance(body, (dict, list)):
            text = json.dumps(body, ensure_ascii=False)
        else:
            text = str(body)
        return " ".join(text.split())[:limit]

    def expect_success(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        token: Optional[str] = None,
        expected_status: int = 200,
    ) -> Any:
        result = self.request(method, path, json_body=json_body, params=params, token=token)
        if result.response.status_code != expected_status:
            raise ApiError(
                f"{method} {path} returned {result.response.status_code}: {self.short_body(result.body)}"
            )
        if not isinstance(result.body, dict):
            raise ApiError(f"{method} {path} returned non-JSON: {self.short_body(result.body)}")
        if result.body.get("code") != 0:
            raise ApiError(f"{method} {path} business error: {self.short_body(result.body)}")
        return result.body.get("data")

    def expect_error(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        token: Optional[str] = None,
        expected_status: int = 400,
        expected_code: int = 1,
    ) -> dict[str, Any]:
        result = self.request(method, path, json_body=json_body, params=params, token=token)
        if result.response.status_code != expected_status:
            raise ApiError(
                f"{method} {path} returned {result.response.status_code}, expected {expected_status}: {self.short_body(result.body)}"
            )
        if not isinstance(result.body, dict):
            raise ApiError(f"{method} {path} returned non-JSON: {self.short_body(result.body)}")
        if result.body.get("code") != expected_code:
            raise ApiError(
                f"{method} {path} returned code={result.body.get('code')}, expected {expected_code}: {self.short_body(result.body)}"
            )
        return result.body

    def expect_plain_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        expected_status: int = 200,
    ) -> dict[str, Any]:
        result = self.request(method, path, params=params)
        if result.response.status_code != expected_status:
            raise ApiError(
                f"{method} {path} returned {result.response.status_code}: {self.short_body(result.body)}"
            )
        if not isinstance(result.body, dict):
            raise ApiError(f"{method} {path} returned non-JSON: {self.short_body(result.body)}")
        return result.body

    def register_user(self, username: str, password: str, *, email: Optional[str] = None) -> dict[str, Any]:
        email = email or f"{username}@example.com"
        data = self.expect_success(
            "POST",
            "/api/user/register",
            json_body={"username": username, "email": email, "password": password},
        )
        if not isinstance(data, dict):
            raise ApiError("POST /api/user/register returned unexpected payload")
        return data

    def login_user(self, username: str, password: str) -> dict[str, Any]:
        data = self.expect_success(
            "POST",
            "/api/user/login",
            json_body={"username": username, "password": password},
        )
        if not isinstance(data, dict):
            raise ApiError("POST /api/user/login returned unexpected payload")
        return data
