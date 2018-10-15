import sys
import uuid
import asyncio
from datetime import datetime
from typing import Optional, Union
from .channel.abstractions import TelemetryChannel
from .entities import (Application,
                       LoggingDevice,
                       Context,
                       Operation,
                       Session,
                       User,
                       Envelope,
                       EventData,
                       TraceData,
                       MetricData,
                       DataPoint,
                       DataPointKind,
                       RequestData,
                       ExceptionData,
                       ExceptionDetails)
from .utils import require_params


COMMON_TAGS = {
    'ai.internal.sdkVersion': 'asynpy3:0.0.1'
}


class AsyncTelemetryClient:
    """Azure Application Insights client using asyncio"""
    __slots__ = ('instrumentation_key',
                 '_context',
                 '_channel')

    def __init__(self,
                 instrumentation_key: str,
                 channel: TelemetryChannel,
                 application: Optional[Application]=None,
                 device: Optional[LoggingDevice]=None):
        require_params(instrumentation_key=instrumentation_key,
                       channel=channel)
        self.instrumentation_key = instrumentation_key
        self._context = Context(application, device)
        self._channel = channel

    def handle_unhandled_exceptions(self, loop=None):
        """
        Registers an handler to log all unhandled exceptions with this telemetry client.

        :param loop: loop to execute asynchronous exception logging, if not given asyncio.get_event_loop() is used
        """
        current_excepthook = sys.excepthook

        if loop is None:
            # use implicit loop
            loop = asyncio.get_event_loop()

        async def log_exception_async(type, value, traceback):
            # NB: flush is needed because in case of unhandled exception the whole process might fall
            await self.track_exception(type, value, traceback)
            await self.flush()

        def local_excepthook(type, value, traceback):
            #
            loop.run_until_complete(log_exception_async(type, value, traceback))

            # call the original method
            current_excepthook(type, value, traceback)

        sys.excepthook = local_excepthook
        pass

    async def push(self, data):
        await self._channel.put(data)

    async def flush(self):
        await self._channel.flush()

    async def __aenter__(self):
        return self

    async def __aexit__(self,
                        exc_type,
                        exc_val,
                        exc_tb):
        await self.dispose()

    def get_tags(self,
                 operation: Optional[Operation]=None,
                 session: Optional[Session]=None,
                 user: Optional[User]=None
                 ) -> dict:
        """
        Returns meta tags to be included in any log.
        ref.
        https://github.com/Microsoft/ApplicationInsights-Home/blob/master/EndpointSpecs/Schemas/Docs/ContextTagKeys.md

        :param operation: optional operation data to log.
        :param session: optional session data to log.
        :param user: optional user data to log.
        :return:
        """
        tags = self._context.device.to_dict()

        if self._context.application:
            tags.update(self._context.application.to_dict())

        if operation:
            tags.update(operation.to_dict())

        if user:
            tags.update(user.to_dict())

        if session:
            tags.update(session.to_dict())

        tags.update(COMMON_TAGS)
        return tags

    async def track_event(self,
                          name,
                          properties=None,
                          measurements=None,
                          *,
                          operation: Optional[Operation] = None,
                          session: Optional[Session] = None,
                          user: Optional[User] = None):
        """
        Logs a single event.

        :param name: event name
        :param properties: event properties
        :param measurements: event measurements
        :param operation: optional operation tags to log
        :param session: optional session tags to log
        :param user: optional user tags to log
        :return:
        """
        data = Envelope(self.instrumentation_key,
                        EventData(name, properties, measurements),
                        self.get_tags(operation, session, user))

        await self.push(data)

    async def track_exception(self,
                              type=None,
                              value=None,
                              tb=None,
                              properties=None,
                              measurements=None,
                              *,
                              operation: Optional[Operation] = None,
                              session: Optional[Session] = None,
                              user: Optional[User] = None,
                              skip_frames: Optional[int] = None):
        """
        Tracks a single exception, trying to obtain information from sys.exc_info if type, value and traceback
        are not given.

        :param type: exception type
        :param value: exception value
        :param tb: traceback object
        :param properties: optional properties
        :param measurements: optional measurements
        :param operation: optional operation tags to log
        :param session: optional session tags to log
        :param user: optional user tags to log
        :param skip_frames: optional number of stack frames to be skipped from log
        """
        if not type or not value or not tb:
            type, value, tb = sys.exc_info()

        if not type or not value or not tb:
            try:
                raise Exception('Technical exception')
            except:
                type, value, tb = sys.exc_info()

        details = ExceptionDetails.from_exception(type, value, tb, skip_frames)

        # Python trace back gives us also portions of source code; useful information
        # the official application insights sdk for Python discards it, but it can be stored
        # in custom data like done here:
        index = 0
        text_portions = {}
        for text in details.texts:
            text_portions[f'code_{index}'] = text
            index += 1

        if properties:
            properties.update(text_portions)
        else:
            properties = text_portions

        data = Envelope(self.instrumentation_key,
                        ExceptionData([details],
                                      properties,
                                      measurements),
                        self.get_tags(operation, session, user))

        await self.push(data)

    async def track_trace(self,
                          name,
                          properties=None,
                          severity: int=1,
                          *,
                          operation: Optional[Operation] = None,
                          session: Optional[Session] = None,
                          user: Optional[User] = None):
        """
        Logs a single trace.

        :param name: trace name
        :param properties: trace properties
        :param severity: severity level, refer to entities.TraceSeverity class
        :param operation: optional operation tags to log
        :param session: optional session tags to log
        :param user: optional user tags to log
        """
        data = Envelope(self.instrumentation_key,
                        TraceData(name, properties, severity),
                        self.get_tags(operation, session, user))

        await self.push(data)

    async def track_metric(self,
                           name: str,
                           value: float,
                           kind: DataPointKind = None,
                           count: Optional[int] = None,
                           min: Optional[float] = None,
                           max: Optional[float] = None,
                           std_dev: Optional[float] = None,
                           properties: Optional[dict] = None,
                           *,
                           operation: Optional[Operation] = None,
                           session: Optional[Session] = None,
                           user: Optional[User] = None
                           ):
        """
        Logs a single metric; measurement or aggregation data.

        :param name: metric name
        :param value: metric value
        :param kind: metric kind (Measurement | Aggregation)
        :param count: optional count
        :param min: optional minimum value
        :param max: optional maximum value
        :param std_dev: optional standard deviation
        :param properties: optional extra properties to log
        :param operation: optional operation tags to log
        :param session: optional session tags to log
        :param user: optional user tags to log
        :return:
        """
        item = DataPoint(name, value, kind, count, min, max, std_dev)

        data = Envelope(self.instrumentation_key,
                        MetricData(item, properties),
                        self.get_tags(operation, session, user))

        await self.push(data)

    async def track_request(self,
                            _id: str,
                            name: str,
                            url: str,
                            success: bool,
                            start_time: datetime=None,
                            duration:Optional[int]=None,
                            response_code:Union[str, int]=None,
                            http_method: str=None,
                            properties: Optional[dict]=None,
                            measurements: Optional[dict]=None,
                            *,
                            operation: Optional[Operation] = None,
                            session: Optional[Session] = None,
                            user: Optional[User] = None
                            ):
        """
        Logs a single HTTP request captured by a web application.

        :param _id: telemetry id assigned to the request
        :param name: the name of request to log
        :param url: actual URL
        :param success: whether the request was processed with success
        :param start_time: request start time when received by the app server
        :param duration: the number of milliseconds it took to process the request
        :param response_code: response code
        :param http_method: request HTTP method
        :param properties: set of custom properties to store
        :param measurements: set of custom measurements to store
        :return:
        """
        if not start_time:
            start_time = datetime.utcnow()

        request_id = _id or str(uuid.uuid4())

        if not operation:
            # in this case, operation tags can be configured automatically if not specified
            # in caller method
            operation = Operation(request_id, f'{http_method} {name}')

        data = Envelope(self.instrumentation_key,
                        RequestData(request_id,
                                    name,
                                    http_method,
                                    url,
                                    response_code,
                                    success,
                                    start_time,
                                    duration or 0,
                                    properties,
                                    measurements),
                        self.get_tags(operation, session, user))

        await self.push(data)

    async def dispose(self):
        try:
            await self._channel.flush()
        finally:
            await self._channel.dispose()
        return self
