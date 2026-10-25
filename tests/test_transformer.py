from payload_cache.services.transformer import transform


def test_uppercase_and_unicode() -> None:
    assert transform("hello") == "HELLO"
    assert transform("mañana") == "MAÑANA"
    assert transform("") == ""
