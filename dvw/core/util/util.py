import numpy as np

__all__ = [
    "bit2sign",
    "around",
    "asplit",
    "shape2shape",
    "isint",
    "isfloat",
    "isnum",
    "isstr",
    "isdict",
    "isarray",
    "tuple2list",
    "aslist",
    "enum_values",
    "alower"
]


def bit2sign(b):
    return 1 if b else -1


def around(iterable, precise):
    return [
        round(x, precise) if type(x) == float else x
        for x in iterable
    ]


def asplit(iterable, separator=':', max_split=2):
    return dict(x.split(separator, max_split) for x in iterable)


def enum_values(enum):
    return [e.value for e in enum]


def tuple2list(x):
    if type(x) == tuple:
        return list(x)
    return x


def aslist(x):
    if isarray(x):
        return list(x)
    return [x]


def shape2shape(shape, height=None, width=None):
    if not width and not height:
        return shape

    if not height:
        height = width * shape[0] // shape[1]
    elif not width:
        width = height * shape[1] // shape[0]

    return height, width


def alower(iterable):
    return [(x.lower() if isstr(x) else x) for x in iterable]


def isint(x):
    return isinstance(x, int) and not isinstance(x, bool)


def isfloat(x):
    return isinstance(x, float)


def isnum(x):
    return isint(x) or isfloat(x)


def isstr(x):
    return isinstance(x, str)


def isdict(x):
    return isinstance(x, dict)


def isarray(x):
    return isinstance(x, (list, tuple, np.ndarray))
