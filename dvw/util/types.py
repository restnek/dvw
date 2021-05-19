from typing import Tuple, Optional, Union, Literal, TypeVar

import numpy as np

T = TypeVar("T")

Shape2d = Tuple[int, int]
Shape2dParameters = Union[Tuple[Optional[int], Optional[int]], Literal[-1], None]
FrameWithReturn = Union[np.ndarray, Tuple[np.ndarray, ...]]
