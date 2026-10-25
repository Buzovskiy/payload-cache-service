from payload_cache.core.config import Settings


def test_database_url_uses_individual_settings() -> None:
    settings = Settings(
        db_host="localhost",
        db_port=5435,
        postgres_user="payload",
        postgres_password="p@ss:word",
        postgres_db="payload_cache",
    )
    url = settings.database_url
    assert url.host == "localhost"
    assert url.port == 5435
    assert url.password == "p@ss:word"
    assert url.database == "payload_cache"
    assert "p%40ss%3Aword" in url.render_as_string(hide_password=False)
