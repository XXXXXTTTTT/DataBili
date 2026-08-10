import asyncio

from healthcheck import check_public_api


def test_healthcheck_returns_observable_result():
    result = asyncio.run(check_public_api(timeout_seconds=1))
    assert {"ok", "http_status", "api_code", "message"}.issubset(result)
