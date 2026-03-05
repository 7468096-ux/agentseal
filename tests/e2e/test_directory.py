import httpx

BASE_URL = "http://54.254.155.94"


def test_directory_page_loads():
    resp = httpx.get(BASE_URL + "/directory", timeout=10)
    assert resp.status_code == 200
    assert "Agent Directory" in resp.text


def test_directory_search_and_filters():
    resp = httpx.get(BASE_URL + "/directory", params={"q": "alice"}, timeout=10)
    assert resp.status_code == 200
    assert "value=\"alice\"" in resp.text

    resp = httpx.get(
        BASE_URL + "/directory",
        params={"platform": "openclaw", "tier": "gold", "sort": "name"},
        timeout=10,
    )
    assert resp.status_code == 200
    html = resp.text
    assert "value=\"openclaw\" selected" in html
    assert "value=\"gold\" selected" in html
    assert "value=\"name\" selected" in html
