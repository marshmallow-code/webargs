import asyncio

import pytest

pytest.register_assert_rewrite("webargs.testing")


@pytest.fixture
def current_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    asyncio.set_event_loop(None)
    loop.close()
