from typing import Iterable

_DIGITAL_SIZE_PREFIXES = ["", "K", "M", "G", "T", "P", "E", "Z", "Y"]
_BITRATE_PREFIXES = ["", "k", "M", "G", "T"]


def size2human(size: float, suffix: str = "B") -> str:
    return _value2human(size, 1024, _DIGITAL_SIZE_PREFIXES, suffix)


def bitrate2human(bitrate: float) -> str:
    return _value2human(bitrate, 1000, _BITRATE_PREFIXES, "bit/s")


def _value2human(
    value: float, factor: int, prefixes: Iterable[str], suffix: str
) -> str:
    for unit in prefixes:
        if value < factor:
            break
        value /= factor
    return f"{value:.2f} {unit}{suffix}"
