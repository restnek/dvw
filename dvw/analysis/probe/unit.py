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