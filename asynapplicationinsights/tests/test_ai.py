import uuid
import asyncio
import unittest
from datetime import datetime, timedelta
from .settings import instrumentation_key
from ..telemetry import AsyncTelemetryClient
from ..channel.aiohttpchannel import AiohttpTelemetryChannel
from random import randint


class TestAi(unittest.TestCase):

    def test_write_event(self):
        loop = asyncio.get_event_loop()

        async def go():
            client = AsyncTelemetryClient(instrumentation_key,
                                          AiohttpTelemetryChannel())

            await client.track_event('Example',
                                     measurements={
                                         'speed': 55.5
                                     })

            await client.track_trace('Foo', {'foo': 'power'}, 2)

            for _ in range(10):
                await asyncio.sleep(0.005)
                await client.track_metric('Something',
                                          randint(0, 200))

            await client.track_request(str(uuid.uuid4()),
                                       'Example',
                                       'http://localhost:44666/like/123456',
                                       True,
                                       datetime.utcnow() + timedelta(seconds=-10),
                                       duration=125,
                                       response_code=200,
                                       http_method='GET'
                                       )

            try:
                x = 100 / 0
            except:
                await client.track_exception()

            await client.flush()
            await client.dispose()

        loop.run_until_complete(go())
