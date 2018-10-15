from ..exceptions import ArgumentNullException


def has_params(data, *args):
    """
    Validates required parameters against an object.

    :param data:
    :param args: required parameters
    :return:
    """
    if not data:
        return False
    for a in args:
        if not a in data:
            return False
        v = data[a]
        if not v or v.isspace():
            return False
    return True


def is_empty_string(value):
    return isinstance(value, str) and value.isspace()


def require_params(*args, **kwargs):
    for name, value in kwargs.items():
        if not value or is_empty_string(value):
            raise ArgumentNullException(name)

    for value in args:
        if not value or is_empty_string(value):
            raise ArgumentNullException(value)
