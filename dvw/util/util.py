import os
from enum import Enum
from pathlib import Path
from typing import Union, List, Iterable, Type

import numpy as np

from dvw.util.types import Shape2d, Shape2dParameters, T


def bit2sign(b: Union[int, bool]) -> int:
    return 1 if b else -1


def enum_values(enum: Type[Enum]) -> list:
    return [e.value for e in enum]


def tuple2list(x: T) -> Union[T, List[T]]:
    if istuple(x):
        return list(x)
    return x


def aslist(x) -> list:
    if isarray(x):
        return list(x)
    return [x]


def shape2shape(old_shape: Shape2d, new_shape: Shape2dParameters = None) -> Shape2d:
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


def isint(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def isfloat(x) -> bool:
    return isinstance(x, float)


def isnum(x) -> bool:
    return isint(x) or isfloat(x)


def isstr(x) -> bool:
    return isinstance(x, str)


def istuple(x) -> bool:
    return isinstance(x, tuple)


def isarray(x) -> bool:
    return isinstance(x, (list, tuple, np.ndarray))


def isdict(x) -> bool:
    return isinstance(x, dict)


def contains(iterable: Iterable, *values) -> bool:
    return all((v in iterable) for v in values)


def create_folder(*paths: str) -> str:
    path = os.path.join(*paths)
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def filename(path: str) -> str:
    return os.path.split(path)[1]
