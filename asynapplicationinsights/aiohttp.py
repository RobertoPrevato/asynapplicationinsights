"""
* aiohttp integration with Azure Application Insights
*
* https://github.com/RobertoPrevato/asynapplicationinsights
*
* Copyright 2018, Roberto Prevato
* https://robertoprevato.github.io
*
* Licensed under the MIT license:
* http://www.opensource.org/licenses/MIT
"""
import uuid
import time
from typing import Optional, Callable
from aiohttp import web, ClientSession
from aiohttp.web_exceptions import HTTPException
from datetime import datetime
from .telemetry import AsyncTelemetryClient
from .entities import Application, LoggingDevice
from .channel.aiohttpchannel import AiohttpTelemetryChannel


def default_time_getter():
    return datetime.utcnow()


# success codes from server perspective!
client_errors_request_handling_success = {401, 403, 404, 405}


def default_is_success_request(status):
    if status < 400:
        return True

    if status in client_errors_request_handling_success:
        # failed from client perspective, but successfully handled by server perspective!
        # such as unauthorized, forbidden, not found
        return True

    return False


def get_request_name(request):
    ascii_encodable_path = request.path.encode('ascii', 'backslashreplace') \
        .decode('ascii')
    return ascii_encodable_path



def use_application_insights(app: web.Application,
                             instrumentation_key: str,
                             app_metadata: Optional[Application] = None,
                             logging_device: Optional[LoggingDevice] = None,
                             time_getter: Optional[Callable] = None,
                             user_getter: Optional[Callable] = None,
                             is_success_request: Optional[Callable] = None,
                             requests_filter: Optional[Callable] = None,
                             client_session: ClientSession=None,
                             loop=None):
    """
    Integrates asynchronous client for Azure Application Insights into an aiohttp application.

    :param app: aiohttp application
    :param instrumentation_key: application insights instrumentation key
    :param app_metadata: optional metadata about the application
    :param logging_device: optional metadata about the logging device; if not specified one is created with platform information
    :param time_getter: optional method to return current time for request, if not specified datetime.utcnow is used
    :param user_getter: optional method to obtain user metadata information from request
    :param is_success_request: optional method to determine whether a request was successful from server perspective
    :param requests_filter: optional method to filter requests from ai logging
    :param loop: optional asyncio loop, if not specified asyncio.get_event_loop is used
    :param client_session: optionally, an http client session for web requests
    :return:
    """
    if loop is None:
        loop = app.loop

    if not time_getter:
        time_getter = default_time_getter

    if not is_success_request:
        is_success_request = default_is_success_request

    client = AsyncTelemetryClient(instrumentation_key,
                                  AiohttpTelemetryChannel(loop, client_session),
                                  app_metadata,
                                  logging_device)

    # on clean up, dispose the client
    async def on_clean_up_dispose_ai_client(_):
        await client.track_event('Application_Stop')
        await client.dispose()

    app.on_cleanup.append(on_clean_up_dispose_ai_client)

    setattr(app, 'ai_client', client)

    @web.middleware
    async def application_insights_middleware(request, handler):

        if requests_filter and requests_filter(request):
            return await handler(request)

        start_datetime = time_getter()
        start = time.time()
        req_name = get_request_name(request)
        req_url = str(request.url)
        telemetry_id = str(uuid.uuid4())
        user_data = None

        request.telemetry_id = telemetry_id

        try:
            response = await handler(request)

            # restore user context if possible, this must happen here
            if user_getter:
                user_data = user_getter(request)

            elapsed = time.time() - start
            elapsed_ms = int(elapsed * 1000)

            success = is_success_request(response.status)
            await client.track_request(telemetry_id,
                                       req_name,
                                       req_url,
                                       success,
                                       start_datetime,
                                       elapsed_ms,
                                       response.status,
                                       request.method,
                                       user=user_data)
            return response
        except HTTPException as http_exception:
            elapsed = time.time() - start
            elapsed_ms = int(elapsed * 1000)

            # restore user context if possible, this must happen here
            if user_getter:
                user_data = user_getter(request)

            status = http_exception.status
            success = is_success_request(status)
            await client.track_request(telemetry_id,
                                       req_name,
                                       req_url,
                                       success,
                                       start_datetime,
                                       elapsed_ms,
                                       status,
                                       request.method,
                                       user=user_data)
            raise
        except Exception as exception:
            # log exception
            elapsed = time.time() - start
            elapsed_ms = int(elapsed * 1000)

            # restore user context if possible, this must happen here
            if user_getter:
                user_data = user_getter(request)

            status = 500
            success = False
            await client.track_request(telemetry_id,
                                       req_name,
                                       req_url,
                                       success,
                                       start_datetime,
                                       elapsed_ms,
                                       status,
                                       request.method,
                                       user=user_data)

            # track exception
            await client.track_exception(exception.__class__,
                                         exception,
                                         exception.__traceback__,
                                         user=user_data,
                                         skip_frames=1)
            raise

    app.middlewares.append(application_insights_middleware)

    return application_insights_middleware

