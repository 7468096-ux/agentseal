from app.services.auth_service import generate_api_key


def test_generate_api_key_format():
    raw, prefix, key_hash = generate_api_key()
    assert raw.startswith("as_live_")
    assert len(prefix) == 8
    assert key_hash
