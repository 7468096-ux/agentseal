import httpx

BASE_URL = "http://54.254.155.94"


def test_profile_page_loads():
    agents = httpx.get(BASE_URL + "/v1/agents", params={"limit": 1}, timeout=10).json()
    assert agents.get("agents"), "expected at least one agent"
    slug = agents["agents"][0]["slug"]

    resp = httpx.get(BASE_URL + f"/@{slug}", timeout=10)
    assert resp.status_code == 200
    html = resp.text
    assert "Trust score" in html
    assert "Seals & badges" in html
    assert "Embed badge" in html
