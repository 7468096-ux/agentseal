import httpx

BASE_URL = "http://54.254.155.94"


def test_landing_page_loads():
    resp = httpx.get(BASE_URL + "/", timeout=10)
    assert resp.status_code == 200
    html = resp.text
    assert "Trust signals for autonomous agents" in html
    assert "Featured agents" in html
    assert "Certifications completed" in html
