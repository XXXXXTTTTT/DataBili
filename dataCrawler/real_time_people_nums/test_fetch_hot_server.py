import asyncio

import fetch_hot_server


def test_record_rejects_non_positive_item_limit():
    try:
        asyncio.run(fetch_hot_server.record(total_items=0))
    except ValueError as error:
        assert str(error) == 'total_items 必须大于 0'
    else:
        raise AssertionError('record 应拒绝非正采集条数')
