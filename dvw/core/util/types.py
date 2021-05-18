from typing import Tuple, Optional, Union, Literal

import numpy as np

Shape = Tuple[int, int]
ShapeParameters = Union[Tuple[Optional[int], Optional[int]], Literal[-1], None]
FrameWithReturn = Union[np.ndarray, Tuple[np.ndarray, ...]]
