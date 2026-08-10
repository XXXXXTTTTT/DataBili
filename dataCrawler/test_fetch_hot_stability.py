import asyncio

import fetch_hot


class DummySession:
    pass


def test_fetch_all_pages_accepts_shared_session(monkeypatch):
    calls = []

    async def fake_fetch_page(session, page, ps, retries=fetch_hot.RETRY_ATTEMPTS):
        calls.append(session)
        return [{"aid": page}]

    monkeypatch.setattr(fetch_hot, "fetch_page", fake_fetch_page)
    session = DummySession()
    result = asyncio.run(fetch_hot.fetch_all_pages(total_items=2, ps=1, session=session))

    assert len(result) == 2
    assert calls == [session, session]
