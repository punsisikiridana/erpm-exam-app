"""Low-level HTTP client for mcqmed.lk's Supabase backend.

NOT YET FUNCTIONAL. This file is a scaffold — see backend/app/importer/README.md
for exactly what's missing and how to fill it in. In short: calling Supabase's
REST API requires an "anon" public API key (sent as the `apikey` header)
in addition to the user's personal access token, and the real table/column
names aren't known yet. Both have to come from inspecting mcqmed.lk's own
app while logged in (e.g. your browser's DevTools Network tab) — an
automated attempt to extract this from the site was blocked by this
session's safety controls as out-of-scope "unauthorized access" to a
third-party backend, so it needs to be done by a human (you) and the
values pasted into .env.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings


class McqmedClient:
    def __init__(self) -> None:
        if not settings.mcqmed_anon_key:
            raise RuntimeError(
                "MCQMED_ANON_KEY is not set. See backend/app/importer/README.md — "
                "this key must be captured from mcqmed.lk's own app (e.g. browser DevTools), "
                "it cannot be derived from your access token alone."
            )
        self._access_token = settings.mcqmed_access_token
        self._refresh_token = settings.mcqmed_refresh_token
        self._anon_key = settings.mcqmed_anon_key
        self._base_url = settings.mcqmed_supabase_url.rstrip("/")
        self._client = httpx.Client(base_url=self._base_url, timeout=30.0)

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self._anon_key,
            "Authorization": f"Bearer {self._access_token}",
        }

    def _refresh(self) -> None:
        resp = self._client.post(
            "/auth/v1/token",
            params={"grant_type": "refresh_token"},
            headers={"apikey": self._anon_key},
            json={"refresh_token": self._refresh_token},
        )
        if resp.status_code != 200:
            raise RuntimeError(
                "mcqmed.lk token refresh failed — the access token has likely expired. "
                "Log in to mcqmed.lk again in your browser and re-export a fresh token."
            )
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token", self._refresh_token)

    def fetch_table(self, table: str, params: dict[str, Any], retry_on_auth_failure: bool = True) -> list[dict]:
        """GET rows from a PostgREST table endpoint, paginating via Range headers.

        `table` and the shape of `params` (e.g. `topic_id=eq.<id>`, `select=...`)
        depend on mcqmed.lk's actual schema, which is not yet known — fill this
        in once you've captured it (see README.md in this directory).
        """
        rows: list[dict] = []
        offset = 0
        page_size = 500
        while True:
            headers = {**self._headers(), "Range-Unit": "items", "Range": f"{offset}-{offset + page_size - 1}"}
            resp = self._client.get(f"/rest/v1/{table}", params=params, headers=headers)
            if resp.status_code == 401 and retry_on_auth_failure:
                self._refresh()
                return self.fetch_table(table, params, retry_on_auth_failure=False)
            resp.raise_for_status()
            page = resp.json()
            rows.extend(page)
            if len(page) < page_size:
                break
            offset += page_size
            time.sleep(0.3)  # be polite to a free, student-run service
        return rows
