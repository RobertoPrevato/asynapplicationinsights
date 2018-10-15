
def exception_str(ex):
    return str(ex) or ex.__class__.__name__


class OperationFailed(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidOperation(Exception):
    """An exception risen in case of an operation that doesn't make sense in a certain context."""


class ArgumentNullException(ValueError):
    """An exception risen when a null or empty parameter is not acceptable."""
    def __init__(self, param_name):
        super().__init__(f'Parameter cannot be null or empty: `{param_name}`')


class InvalidArgument(Exception):
    pass
