import httpx

BASE_URL = "http://3.0.92.255"


def test_core_api_endpoints():
    agents_resp = httpx.get(BASE_URL + "/v1/agents", params={"limit": 1}, timeout=10)
    assert agents_resp.status_code == 200
    agents = agents_resp.json()
    assert agents.get("agents"), "expected at least one agent"

    slug = agents["agents"][0]["slug"]
    agent_resp = httpx.get(BASE_URL + f"/v1/agents/by-slug/{slug}", timeout=10)
    assert agent_resp.status_code == 200

    seals_resp = httpx.get(BASE_URL + "/v1/seals", timeout=10)
    assert seals_resp.status_code == 200
    assert "seals" in seals_resp.json()

    cert_resp = httpx.get(BASE_URL + "/v1/certifications", timeout=10)
    assert cert_resp.status_code == 200
    assert "tests" in cert_resp.json()
