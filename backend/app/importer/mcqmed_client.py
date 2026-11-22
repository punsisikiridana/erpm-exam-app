"""Low-level HTTP client for mcqmed.lk's Supabase backend.

Schema discovered by inspecting the app's own Network tab while logged in
(the user captured this manually; no automated access to mcqmed.lk's
internals was used):

- GET  /rest/v1/questions?select=id,sort_order,type&is_active=eq.true
       &topic_id=in.(<topic-uuid>)&order=id.asc&offset=N&limit=1000
  -> list of {id, sort_order, type} for every active question in a topic.

- POST /rest/v1/rpc/get_questions  body: {"p_ids": [<question-uuid>, ...]}
  -> list of full question objects:
     {id, stem, type ("sba"|"true_false"),
      answers: [{id, body, is_correct, sort_order}, ...],
      explanation}

Both need the `apikey` header (mcqmed's public Supabase anon/publishable
key — not secret, it ships in every visitor's browser) plus the user's own
personal `Authorization: Bearer <access_token>`.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings

_PAGE_SIZE = 50  # questions per get_questions call — keep request bodies modest


class McqmedClient:
    def __init__(self) -> None:
        if not settings.mcqmed_anon_key:
            raise RuntimeError(
                "MCQMED_ANON_KEY is not set. See backend/app/importer/README.md."
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
            headers={"apikey": self._anon_key, "Content-Type": "application/json"},
            json={"refresh_token": self._refresh_token},
        )
        if resp.status_code != 200:
            raise RuntimeError(
                "mcqmed.lk token refresh failed — the access token has likely expired. "
                "Log in to mcqmed.lk again in your browser and re-capture a fresh token "
                "(see backend/app/importer/README.md)."
            )
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token", self._refresh_token)

    def list_topic_question_ids(self, topic_id: str) -> list[dict[str, Any]]:
        """Returns [{id, sort_order, type}, ...] for every active question in a topic."""
        rows: list[dict] = []
        offset = 0
        limit = 1000
        while True:
            resp = self._client.get(
                "/rest/v1/questions",
                params={
                    "select": "id,sort_order,type",
                    "is_active": "eq.true",
                    "topic_id": f"in.({topic_id})",
                    "order": "id.asc",
                    "offset": offset,
                    "limit": limit,
                },
                headers=self._headers(),
            )
            if resp.status_code == 401:
                self._refresh()
                resp = self._client.get(
                    "/rest/v1/questions",
                    params={
                        "select": "id,sort_order,type",
                        "is_active": "eq.true",
                        "topic_id": f"in.({topic_id})",
                        "order": "id.asc",
                        "offset": offset,
                        "limit": limit,
                    },
                    headers=self._headers(),
                )
            resp.raise_for_status()
            page = resp.json()
            rows.extend(page)
            if len(page) < limit:
                break
            offset += limit
        return rows

    def get_questions(self, ids: list[str]) -> list[dict[str, Any]]:
        """Bulk-fetch full question content for a list of question ids, paginated."""
        out: list[dict] = []
        for i in range(0, len(ids), _PAGE_SIZE):
            chunk = ids[i : i + _PAGE_SIZE]
            resp = self._client.post(
                "/rest/v1/rpc/get_questions",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"p_ids": chunk},
            )
            if resp.status_code == 401:
                self._refresh()
                resp = self._client.post(
                    "/rest/v1/rpc/get_questions",
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json={"p_ids": chunk},
                )
            resp.raise_for_status()
            out.extend(resp.json())
            time.sleep(0.3)  # be polite to a free, student-run service
        return out
