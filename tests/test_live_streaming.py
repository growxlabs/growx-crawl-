import asyncio
import pytest
from growx_crawl.events import CrawlEvent, CrawlEventBroadcaster
from growx_crawl.web.app import app


def test_crawl_event_broadcaster_pub_sub():
    job_id = "test_job_sse_1"
    q = CrawlEventBroadcaster.subscribe(job_id)

    event1 = CrawlEvent(event="job_started", job_id=job_id, data={"query": "test query"})
    CrawlEventBroadcaster.publish(event1)

    assert q.qsize() == 1
    received = q.get_nowait()
    assert received.event == "job_started"
    assert received.job_id == job_id
    assert received.data["query"] == "test query"

    recent = CrawlEventBroadcaster.get_recent_events(job_id)
    assert len(recent) >= 1
    assert recent[-1].event == "job_started"

    CrawlEventBroadcaster.unsubscribe(job_id, q)


@pytest.mark.asyncio
async def test_sse_endpoint_response_headers():
    import httpx
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Perform a request to activity endpoint
        res = await client.get("/api/jobs/job_123/activity")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
