from __future__ import annotations

import asyncio
import pytest
import aiohttp

# Import only the retry helper, not the full coordinator (which pulls in HA)
# We reproduce the same logic here to test it in isolation.
_NETWORK_ERRORS = (aiohttp.ClientError, asyncio.TimeoutError, OSError)


async def _with_retry(coro_fn, retries: int = 2, base_delay: float = 0.0):
    """Mirror of coordinator._with_retry with zero base_delay for fast tests."""
    for attempt in range(retries + 1):
        try:
            return await coro_fn()
        except _NETWORK_ERRORS:
            if attempt == retries:
                raise
            await asyncio.sleep(base_delay * (2 ** attempt))


class TestWithRetry:
    async def test_returns_result_on_first_attempt(self):
        calls = []

        async def ok():
            calls.append(1)
            return "success"

        result = await _with_retry(ok)
        assert result == "success"
        assert len(calls) == 1

    async def test_retries_on_client_error(self):
        calls = []

        async def flaky():
            calls.append(1)
            if len(calls) < 2:
                raise aiohttp.ClientConnectionError("connection refused")
            return "ok"

        result = await _with_retry(flaky)
        assert result == "ok"
        assert len(calls) == 2

    async def test_retries_on_timeout(self):
        calls = []

        async def slow():
            calls.append(1)
            if len(calls) < 2:
                raise asyncio.TimeoutError()
            return "ok"

        result = await _with_retry(slow)
        assert result == "ok"

    async def test_raises_after_max_retries(self):
        async def always_fail():
            raise aiohttp.ClientConnectionError("always fails")

        with pytest.raises(aiohttp.ClientConnectionError):
            await _with_retry(always_fail, retries=2)

    async def test_does_not_retry_value_error(self):
        calls = []

        async def bad_data():
            calls.append(1)
            raise ValueError("bad JSON")

        with pytest.raises(ValueError):
            await _with_retry(bad_data)
        assert len(calls) == 1  # must not retry non-network errors

    async def test_retries_os_error(self):
        calls = []

        async def network_issue():
            calls.append(1)
            if len(calls) < 3:
                raise OSError("network unreachable")
            return "recovered"

        result = await _with_retry(network_issue, retries=2)
        assert result == "recovered"
        assert len(calls) == 3
