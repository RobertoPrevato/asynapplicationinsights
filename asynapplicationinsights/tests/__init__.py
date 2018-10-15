import unittest


def cases(*cases):
    def decorator(f):
        f.cases = cases
        return f
    return decorator


def _apply(func, args):
    """Return a function with args applied after first argument"""
    def wrapped(self):
        return func(self, *args)
    return wrapped


class TheoryMeta(type):
    """Metaclass that replaces test methods with multiple methods for each test case"""
    def __new__(meta, name, bases, attrs):
        newattrs = {}

        for name, value in attrs.items():
            if not name.startswith('test') or not callable(value):
                newattrs[name] = value
                continue

            if not hasattr(value, 'cases'):
                newattrs[name] = value
                continue

            cases = value.cases

            for n, args in enumerate(cases):
                test_name = '%s_%d' % (name, n)
                newattrs[test_name] = _apply(value, args)

        return super().__new__(meta, name, bases, newattrs)


class Theory(unittest.TestCase, metaclass=TheoryMeta):
    pass
