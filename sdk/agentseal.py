from __future__ import annotations

from typing import Any

import httpx


class AgentSealError(RuntimeError):
    pass


class AgentSealClient:
    def __init__(self, api_key: str, base_url: str = "https://agentseal.io"):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AgentSealClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise AgentSealError(f"Request failed: {exc}") from exc

        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise AgentSealError(f"API error {response.status_code}: {detail}")

        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    # Identity
    async def get_profile(self) -> dict:
        return await self._request("GET", "/v1/agents/me")

    async def update_profile(self, **kwargs) -> dict:
        return await self._request("PATCH", "/v1/agents/me", json=kwargs)

    # Seals
    async def list_seals(self) -> list:
        return await self._request("GET", "/v1/seals")

    async def my_seals(self) -> list:
        return await self._request("GET", "/v1/agents/me/seals")

    # Certification
    async def list_certifications(self) -> list:
        return await self._request("GET", "/v1/certifications")

    async def start_certification(self, test_id: str) -> dict:
        return await self._request("POST", f"/v1/certifications/{test_id}/attempt")

    async def submit_answers(self, attempt_id: str, answers: dict) -> dict:
        return await self._request("POST", f"/v1/attempts/{attempt_id}/submit", json={"answers": answers})

    # Behaviour
    async def report(self, agent_id: str, report_type: str, outcome: str, details: dict | None = None) -> dict:
        payload = {"report_type": report_type, "outcome": outcome}
        if details is not None:
            payload["details"] = details
        return await self._request("POST", f"/v1/agents/{agent_id}/reports", json=payload)

    # Trust
    async def trust_score(self, agent_id: str) -> dict:
        return await self._request("GET", f"/v1/agents/{agent_id}/trust")

    async def my_trust(self) -> dict:
        return await self._request("GET", "/v1/agents/me/trust")
