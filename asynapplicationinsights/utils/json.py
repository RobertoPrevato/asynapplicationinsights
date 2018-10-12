"""
This module defines a more user-friendly json encoder, supporting time objects and UUID
"""
import json
from datetime import time, date, datetime
from uuid import UUID


class FriendlyEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if isinstance(obj, time):
            return obj.strftime("%H:%M:%S")
        if isinstance(obj, datetime):
            return obj.isoformat() + 'Z'
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, bytes):
            return obj.decode('utf8')
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def friendly_dumps(obj, skipkeys=False, ensure_ascii=False, check_circular=True,
        allow_nan=True, cls=None, indent=None, separators=None,
        default=None, sort_keys=False, **kw):
    if cls is None:
        cls = FriendlyEncoder
    return json.dumps(obj,
                      skipkeys=skipkeys,
                      ensure_ascii=ensure_ascii,
                      check_circular=check_circular,
                      allow_nan=allow_nan,
                      cls=cls,
                      indent=indent,
                      separators=separators,
                      default=default,
                      sort_keys=sort_keys,
                      **kw)
