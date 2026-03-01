from app.services.agent_service import slugify


def test_slugify():
    assert slugify("Alice V3") == "alice-v3"
    assert slugify("Agent!Seal") == "agentseal"
