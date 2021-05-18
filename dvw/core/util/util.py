from enum import Enum
from typing import Union, Any, List, Iterable, Type, TypeVar, Dict, Optional

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
    "istuple",
    "tuple2list",
    "aslist",
    "enum_values",
    "alower",
]

from dvw.core.util.types import Shape, ShapeParameters

T = TypeVar("T")


def bit2sign(b: Union[int, bool]) -> int:
    return 1 if b else -1


def around(iterable: Iterable[Any], precise: int) -> List[Any]:
    return [round(x, precise) if type(x) == float else x for x in iterable]


def asplit(iterable: Iterable[str], separator: Optional[str] = ":") -> Dict[str, str]:
    return dict(x.split(separator, 2) for x in iterable)


def enum_values(enum: Type[Enum]) -> List[Any]:
    return [e.value for e in enum]


def tuple2list(x: T) -> Union[T, List[T]]:
    if type(x) == tuple:
        return list(x)
    return x


def aslist(x: Any) -> List[Any]:
    if isarray(x):
        return list(x)
    return [x]


def shape2shape(old_shape: Shape, new_shape: ShapeParameters = None) -> Shape:
    if new_shape == -1:
        return old_shape[::-1]

    if not new_shape or (not new_shape[0] and not new_shape[1]):
        return old_shape

    height, width = new_shape
    if not height:
        height = width * old_shape[0] // old_shape[1]
    elif not width:
        width = height * old_shape[1] // old_shape[0]

    return height, width


def alower(iterable: Iterable[Any]) -> List[Any]:
    return [(x.lower() if isstr(x) else x) for x in iterable]


def isint(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def isfloat(x: Any) -> bool:
    return isinstance(x, float)


def isnum(x: Any) -> bool:
    return isint(x) or isfloat(x)


def isstr(x: Any) -> bool:
    return isinstance(x, str)


def istuple(x: Any) -> bool:
    return isinstance(x, tuple)


def isarray(x: Any) -> bool:
    return isinstance(x, (list, tuple, np.ndarray))


def isdict(x: Any) -> bool:
    return isinstance(x, dict)
