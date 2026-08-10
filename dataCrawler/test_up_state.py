from bilibili_api.exceptions import NetworkException
from datetime import datetime, timedelta

from up_state import classify_exception, retry_time_passed


def test_classify_http_412_as_risk_blocked():
    status, code = classify_exception(NetworkException(412, "security control policy"))

    assert status == "risk_blocked"
    assert code == 412


def test_classify_unknown_exception_as_provider_error():
    status, code = classify_exception(ValueError("temporary failure"))

    assert status == "provider_error"
    assert code is None


def test_retry_time_passed_only_after_cooldown():
    now = datetime(2026, 8, 10, 20, 0, 0)

    assert retry_time_passed(None, now)
    assert not retry_time_passed(now + timedelta(seconds=1), now)
    assert retry_time_passed(now - timedelta(seconds=1), now)
