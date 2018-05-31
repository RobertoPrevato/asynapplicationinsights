import logging
import locale
import platform
import traceback
from typing import Optional, List
from datetime import datetime
from enum import Enum

#
# NB: for schemas refer to location below
# https://github.com/Microsoft/ApplicationInsights-Home/blob/master/EndpointSpecs/Schemas/Bond/
#
# NB: for tags keys refer to documentation in location below
# https://github.com/Microsoft/ApplicationInsights-Home/blob/master/EndpointSpecs/Schemas/Docs/ContextTagKeys.md


class Operation:
    __slots__ = ('id', 'name')

    def __init__(self, _id: str, name: str):
        self.id = _id
        self.name = name

    def to_dict(self):
        return {
            'ai.operation.id': self.id,
            'ai.operation.name': self.name
        }


class Session:
    __slots__ = ('id',)

    def __init__(self, _id: str):
        """Session ID - the instance of the user's interaction with the app."""
        self.id = _id

    def to_dict(self):
        return {
            'ai.session.id': self.id
        }


class User:
    __slots__ = ('account_id', 'id', 'session_id')

    def __init__(self, account_id: str, _id: str, session_id: str):
        self.account_id = account_id
        self.id = _id  # Anonymous user id. ???!
        self.session_id = session_id

    def to_dict(self):
        data = {}

        if self.account_id:
            data['ai.user.accountId'] = self.account_id

        if self.session_id:
            data['ai.session.id'] = self.session_id

        if self.id:
            data['ai.user.id'] = self.id
        return data


class LoggingDevice:
    """Information about the device that is logging information to Application Insights"""

    __slots__ = ('id', 'type_name', 'os_version', 'locale')

    def __init__(self, type_name=None):
        self.id = platform.node()
        self.type_name = type_name or 'PC'
        self.os_version = platform.version()
        self.locale = locale.getdefaultlocale()[0]

    def to_dict(self):
        return {
            'ai.device.id': self.id,
            'ai.device.locale': self.locale,
            'ai.device.osVersion': self.os_version,
            'ai.device.type': self.type_name
        }


class Application:
    __slots__ = ('version',)

    def __init__(self, version: str):
        self.version = version

    def to_dict(self):
        return {
            'ai.application.ver': self.version
        }


class Context:
    """Telemetry client context, common to all collected telemetries"""
    __slots__ = ('application', 'device')

    def __init__(self,
                 application: Optional[Application]=None,
                 device: Optional[LoggingDevice]=None):
        self.application = application
        self.device = device or LoggingDevice()


class TraceSeverity:
    verbose = 0

    information = 1

    warning = 2

    error = 3

    critical = 4


class TraceData:
    """
    NB: this class is called 'trace' in Azure Portal and anywhere else;
    somebody in Microsoft must have disliked the choice of using such generic names like 'Message'
    """
    envelope_type_name = 'Microsoft.ApplicationInsights.Message'

    data_type_name = 'MessageData'

    logging_levels = {
        'DEBUG': 0,
        'INFO': 1,
        'WARNING': 2,
        'ERROR': 3,
        'CRITICAL': 4,
        logging.DEBUG: 0,
        logging.INFO: 1,
        logging.WARNING: 2,
        logging.ERROR: 3,
        logging.CRITICAL: 4
    }

    __slots__ = ('message', 'properties', 'severity')

    def __init__(self, message: str, properties: Optional[dict]=None, severity: int=1):
        self.message = message
        self.properties = properties
        self.severity = severity

    def to_dict(self):
        return {
            'message': self.message,
            'properties': self.properties,
            'severityLevel': self.severity
        }


class EventData:
    envelope_type_name = 'Microsoft.ApplicationInsights.Event'

    data_type_name = 'EventData'

    __slots__ = ('name', 'properties', 'measurements')

    def __init__(self,
                 name: str,
                 properties: dict,
                 measurements: dict):
        self.name = name
        self.properties = properties
        self.measurements = measurements

    def to_dict(self):
        return {
            'name': self.name,
            'properties': self.properties,
            'measurements': self.measurements
        }


class StackFrame:

    __slots__ = ('level',
                 'method',
                 'module',
                 'file_name',
                 'line')

    def __init__(self,
                 level: int,
                 method: str,
                 module: str,
                 file_name: str,
                 line: int):
        self.level = level
        self.method = method
        # in .NET there are assemblies, in Python not such a thing, but we can log modules
        self.module = module
        self.file_name = file_name
        self.line = line

    def to_dict(self):
        return {
            'level': self.level,
            'method': self.method,
            'assembly': self.module,
            'fileName': self.file_name,
            'line': self.line
        }


class ExceptionDetails:

    __slots__ = ('id',
                 'outer_id',
                 'message',
                 'type_name',
                 'has_full_stack',
                 'stack',
                 'texts')

    def __init__(self,
                 _id: int,
                 type_name: str,
                 message: str,
                 stack: List[StackFrame],
                 texts: List[str]=None,
                 outer_id: int = 0,
                 has_full_stack: bool = True):
        self.id = _id
        self.outer_id = outer_id
        self.type_name = type_name
        self.message = message
        self.has_full_stack = has_full_stack
        self.stack = stack
        self.texts = texts

    @classmethod
    def from_exception(cls, type, value, tb, skip_frames=0):
        _id = 1
        outer_id = 0
        type_name = type.__name__
        message = str(value)

        stack = []
        texts = []
        index = 0
        for tb_frame_file, tb_frame_line, tb_frame_function, tb_frame_text in traceback.extract_tb(tb):
            if skip_frames:
                skip_frames -= 1
                continue

            texts.append(tb_frame_text)

            stack.append(StackFrame(index,
                                    tb_frame_function,
                                    ' ',
                                    tb_frame_file,
                                    tb_frame_line))
            index += 1

        stack.reverse()
        texts.reverse()
        return cls(_id,
                   type_name,
                   message,
                   stack,
                   texts,
                   outer_id,
                   True)

    def to_dict(self):
        return {
            'id': self.id,
            'outerId': self.outer_id,
            'typeName': self.type_name,
            'message': self.message,
            'hasFullStack': self.has_full_stack,
            'parsedStack': self.stack
        }


class ExceptionData:
    envelope_type_name = 'Microsoft.ApplicationInsights.Exception'

    data_type_name = 'ExceptionData'

    __slots__ = ('exceptions', 'properties', 'measurements')

    def __init__(self,
                 exceptions: List[ExceptionDetails],
                 properties: Optional[dict] = None,
                 measurements: Optional[dict] = None):
        self.exceptions = exceptions
        self.properties = properties
        self.measurements = measurements

    def to_dict(self):
        data = {
            'handledAt': 'UserCode',
            'exceptions': self.exceptions
        }

        for name in ('properties', 'measurements'):
            v = getattr(self, name)
            if v:
                data[name] = v

        return data


class DataPointKind(Enum):
    Measurement = 1,
    Aggregation = 2

    def __int__(self):
        return self.value[0]

class DataPointTypes:
    Measurement = 1
    Aggregation = 2


class DataPoint:
    __slots__ = ('name',
                 'kind',
                 'value',
                 'count',
                 'min',
                 'max',
                 'std_dev')

    def __init__(self,
                 name: str,
                 value: float,
                 kind: DataPointKind=None,
                 count: Optional[int]=None,
                 min: Optional[float]=None,
                 max: Optional[float]=None,
                 std_dev: Optional[float]=None):
        # NB
        # https://github.com/Microsoft/ApplicationInsights-Home/blob/master/EndpointSpecs/Schemas/Bond/DataPoint.bond
        if kind is None:
            kind = DataPointKind.Measurement

        self.name = name
        self.kind = kind
        self.value = value
        self.count = count
        self.min = min
        self.max = max
        self.std_dev = std_dev

    def to_dict(self):
        return {x: v for x, v in {
            'name': self.name,
            'value': self.value,
            'kind': int(self.kind),
            'count': self.count,
            'min': self.min,
            'max': self.max,
            'stdDev': self.std_dev
        }.items() if v is not None}


class MetricData:
    envelope_type_name = 'Microsoft.ApplicationInsights.Metric'

    data_type_name = 'MetricData'

    __slots__ = ('item', 'properties')

    def __init__(self, item: DataPoint, properties):
        self.item = item
        self.properties = properties

    def to_dict(self):
        # Metrics document schema defines an array of metrics.
        # However Application Insights only supports one element in this array. (D'oh!)
        return {
            'metrics': [self.item],
            'properties': self.properties
        }


class RequestData:
    envelope_type_name = 'Microsoft.ApplicationInsights.Request'

    data_type_name = 'RequestData'

    __slots__ = ('id',
                 'url',
                 'name',
                 'start_time',
                 'duration',
                 'response_code',
                 'success',
                 'http_method',
                 'properties',
                 'measurements')

    def __init__(self,
                 _id: str,
                 name: str,
                 http_method: str,
                 url: str,
                 response_code: str,
                 success: bool,
                 start_time: datetime,
                 duration: int,
                 properties: Optional[dict],
                 measurements: Optional[dict]):
        self.id = _id
        self.url = url
        self.name = name
        self.start_time = start_time
        self.duration = duration
        self.response_code = int(response_code)
        self.success = success
        self.http_method = http_method
        self.properties = properties
        self.measurements = measurements

    @staticmethod
    def format_duration(duration: int):
        #
        # Application Insights expect this format: hh:mm:ss.fff
        #
        if not duration:
            duration = 0

        if duration < 0:
            raise ValueError('request duration cannot be negative')

        parts = []
        for multiplier in [1000, 60, 60, 24]:
            parts.append(duration % multiplier)
            duration //= multiplier
        parts.reverse()
        formatted_duration = '%02d:%02d:%02d.%03d' % tuple(parts)

        if duration:
            formatted_duration = '%d.%s' % (duration, formatted_duration)

        return formatted_duration

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'startTime': self.start_time,
            'duration': self.format_duration(self.duration),
            'responseCode': str(self.response_code),
            'success': self.success,
            'httpMethod': self.http_method,
            'url': self.url
        }

        if self.properties:
            data['properties'] = self.properties

        if self.measurements:
            data['measurements'] = self.measurements

        return data


class Envelope:

    __slots__ = ('data',
                 'name',
                 'data_type_name',
                 'time',
                 'instrumentation_key',
                 'tags')

    def __init__(self,
                 instrumentation_key: str,
                 data,
                 tags: dict):
        self.data = data
        self.name = data.envelope_type_name
        self.data_type_name = data.data_type_name
        self.time = datetime.utcnow()
        self.instrumentation_key = instrumentation_key
        self.tags = tags

    def __repr__(self):
        return f'<Envelope {self.data_type_name}>'

    def to_dict(self):
        data = self.data.to_dict()
        data['ver'] = 2
        return {
            'ver': 1,
            'name': self.name,
            'time': self.time,
            'sampleRate': 100.00,
            'iKey': self.instrumentation_key,
            'tags': self.tags,
            'data': {
                'baseType': self.data_type_name,
                'baseData': data
            }
        }