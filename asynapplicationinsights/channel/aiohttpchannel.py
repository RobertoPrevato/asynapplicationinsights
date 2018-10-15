import aiohttp
import asyncio
from typing import Optional, List
from .abstractions import TelemetryChannel
from ..exceptions import OperationFailed
from ..utils.json import friendly_dumps


class AiohttpTelemetryChannel(TelemetryChannel):

    def __init__(self,
                 loop:Optional[asyncio.AbstractEventLoop]=None,
                 client:Optional[aiohttp.ClientSession]=None,
                 endpoint:Optional[str]=None):
        super().__init__()

        dispose_client = True
        if client is None:
            if loop is None:
                loop = asyncio.get_event_loop()
            client = aiohttp.ClientSession(loop=loop)
        else:
            dispose_client = False

        if not endpoint:
            endpoint = 'https://dc.services.visualstudio.com/v2/track'

        self._dispose_client = dispose_client
        self._http_client = client
        self._endpoint = endpoint
        self._headers = {'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8'}

    async def send(self, data: List):
        body = friendly_dumps(data)
        response = await self._http_client.post(self._endpoint,
                                                data=body.encode('utf8'),
                                                headers=self._headers)

        if response.status != 200:
            text = await response.text()
            raise OperationFailed(f'Response status does not indicate success: {response.status}; response body: {text}')

    async def dispose(self):
        # NB: the client is disposed only if it was instantiated
        if self._dispose_client:
            await self._http_client.close()
