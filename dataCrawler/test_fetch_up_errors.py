from bilibili_api.exceptions import NetworkException

import fetch_up


def test_network_exception_uses_http_status_for_risk_detection():
    exception = NetworkException(412, 'security control policy')

    assert fetch_up.get_api_error_code(exception) == 412
