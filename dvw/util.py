_DIGITAL_SIZE_PREFIXES = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
_BITRATE_PREFIXES = ['', 'k', 'M', 'G', 'T']


def size2human(size, suffix='B'):
    return _value2human(size, 1024, _DIGITAL_SIZE_PREFIXES, suffix)


def bitrate2human(bitrate):
    return _value2human(bitrate, 1000, _BITRATE_PREFIXES, 'bit/s')


def _value2human(value, factor, prefixes, suffix):
    for unit in prefixes:
        if value < factor:
            break
        value /= factor
    return f'{value:.2f} {unit}{suffix}'


def bit2sign(b):
    return 1 if b else -1


def middle(a, b, c):
    mn = min(a, b, c)
    mx = max(a, b, c)
    if mn <= a <= mx:
        return a, 0
    elif mx <= b <= mx:
        return b, 1
    return c, 2


def around(iterable, precise):
    return [
        round(x, precise) if type(x) == float else x
        for x in iterable
    ]


def get(value, default):
    return default if value is None else value


def asplit(iterable, separator=':', maxsplit=2):
    return dict(x.split(separator, maxsplit) for x in iterable)
