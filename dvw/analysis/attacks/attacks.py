from abc import ABC
from enum import Enum
from typing import Optional, Type

import cv2
import numpy as np

from dvw.core.io import VideoTunnel
from dvw.core.io.video import FrameHandler
from dvw.core.transforms import Transformation
from dvw.core.util import shape2shape
from dvw.core.util.types import ShapeParameters, Shape


class FlipAxis(Enum):
    HORIZONTAL = ("hr", 1)
    VERTICAL = ("vr", 0)
    BOTH = ("both", -1)

    def __new__(cls, value: str, code: int) -> "FlipAxis":
        obj = object().__new__(cls)
        obj._value_ = value
        obj.code = code
        return obj


class RotateAngle(Enum):
    ROTATE_90_CLOCKWISE = (90, 0)
    ROTATE_180 = (180, 1)
    ROTATE_90_COUNTERCLOCKWISE = (270, 2)

    def __new__(cls, value: int, code: int) -> "RotateAngle":
        obj = object().__new__(cls)
        obj._value_ = value
        obj.code = code
        return obj


class Attack(Transformation, FrameHandler, ABC):
    @property
    def shape(self) -> ShapeParameters:
        return None

    def transform(self, domain: np.ndarray, memory: list) -> np.ndarray:
        return self.handle(domain)

    def restore(self, domain: np.ndarray, memory: list) -> np.ndarray:
        return domain


class Flip(Attack):
    def __init__(self, axis: FlipAxis) -> None:
        self.axis = axis

    def handle(self, frame: np.ndarray) -> np.ndarray:
        return cv2.flip(frame, self.axis.code)


class Resize(Attack):
    def __init__(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> None:
        self.width = width
        self.height = height

    @property
    def shape(self) -> Shape:
        return self.height, self.width

    def handle(self, frame: np.ndarray) -> np.ndarray:
        shape = shape2shape(np.shape(frame), (self.height, self.width))
        return cv2.resize(frame, shape[::-1])


class Crop(Attack):
    def __init__(self, y: int, x: int, height: int, width: int) -> None:
        self.y1 = y
        self.y2 = y + height
        self.x1 = x
        self.x2 = x + width

    @property
    def shape(self) -> Shape:
        return self.y2 - self.y1, self.x2 - self.x1

    def handle(self, frame: np.ndarray) -> np.ndarray:
        frame = np.array(frame)
        return frame[self.y1 : self.y2, self.x1 : self.x2]


class Fill(Attack):
    def __init__(self, y: int, x: int, height: int, width: int, value: int) -> None:
        self.y1 = y
        self.y2 = y + height
        self.x1 = x
        self.x2 = x + width
        self.value = value

    def handle(self, frame: np.ndarray) -> np.ndarray:
        frame = np.array(frame)
        frame[self.y1 : self.y2, self.x1 : self.x2] = self.value
        return frame


class Rotate(Attack):
    def __init__(self, angle: RotateAngle) -> None:
        self.angle = angle

    @property
    def shape(self) -> ShapeParameters:
        if RotateAngle.ROTATE_180 != self.angle:
            return -1
        return None

    def handle(self, frame: np.ndarray) -> np.ndarray:
        return cv2.rotate(frame, self.angle.code)


class Gaussian(Attack):
    def __init__(self, std: float = 1, area: float = 1) -> None:
        self.std = std
        self.area = area

    def handle(self, frame: np.ndarray) -> np.ndarray:
        frame = np.array(frame, dtype=float)
        if self.area >= 1:
            frame.flat += np.random.normal(0, self.std, frame.size)
        elif self.area > 0:
            amount = int(self.area * frame.size)
            flat_indices = np.random.choice(frame.size, amount, False)
            frame.flat[flat_indices] += np.random.normal(0, self.std, amount)
        return frame.clip(0, 255).astype(np.uint8)


class SaltAndPepper(Attack):
    def __init__(self, area: float = 1) -> None:
        self.area = area

    def handle(self, frame: np.ndarray) -> np.ndarray:
        frame = frame.copy()
        height, width = frame.shape[:2]
        total = height * width
        amount = int(self.area * total)

        flat_idx = np.random.choice(total, amount, False)
        flat_salt = flat_idx[: len(flat_idx) // 2]
        flat_pepper = flat_idx[len(flat_idx) // 2 :]

        salt = np.unravel_index(flat_salt, (height, width))
        pepper = np.unravel_index(flat_pepper, (height, width))

        frame[salt] = 255
        frame[pepper] = 0

        return frame


def attack_video(
    attack: Attack,
    input_path: str,
    output_path: str,
    codec: str = "mp4v",
    fps: Optional[int] = None,
) -> None:
    with VideoTunnel(input_path, output_path, codec, fps, attack.shape) as video_tunnel:
        video_tunnel.transfer_all(attack)


def name2class(name: str) -> Type[Attack]:
    return _ATTACKS.get(name)


_ATTACKS = {
    "flip": Flip,
    "resize": Resize,
    "crop": Crop,
    "fill": Fill,
    "rotate": Rotate,
    "gaussian": Gaussian,
    "salt-and-pepper": SaltAndPepper,
}
