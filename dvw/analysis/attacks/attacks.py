from enum import Enum

import cv2
import numpy as np

from dvw.core.io import VideoTunnel
from dvw.core.io.video import FrameHandler
from dvw.core.util import shape2shape


class FlipAxis(Enum):
    HORIZONTAL = ('hr', 1)
    VERTICAL = ('vr', 0)
    BOTH = ('both', -1)

    def __new__(cls, value, code):
        obj = object().__new__(cls)
        obj._value_ = value
        obj.code = code
        return obj


class RotateAngle(Enum):
    ROTATE_90_CLOCKWISE = (90, 0)
    ROTATE_180 = (180, 1)
    ROTATE_90_COUNTERCLOCKWISE = (270, 2)

    def __new__(cls, value, code):
        obj = object().__new__(cls)
        obj._value_ = value
        obj.code = code
        return obj


class Flip(FrameHandler):
    def __init__(self, axis: FlipAxis):
        self.axis = axis

    def handle(self, frame):
        return cv2.flip(frame, self.axis.code)


class Resize(FrameHandler):
    def __init__(self, width=None, height=None):
        self.width = width
        self.height = height

    def handle(self, frame):
        shape = shape2shape(np.shape(frame), self.height, self.width)
        return cv2.resize(frame, shape[::-1])


class Crop(FrameHandler):
    def __init__(self, y, x, height, width):
        self.y1 = y
        self.y2 = y + height
        self.x1 = x
        self.x2 = x + width

    def handle(self, frame):
        frame = np.array(frame)
        return frame[self.y1:self.y2, self.x1:self.x2]


class Fill(FrameHandler):
    def __init__(self, y, x, height, width, value):
        self.y1 = y
        self.y2 = y + height
        self.x1 = x
        self.x2 = x + width
        self.value = value

    def handle(self, frame):
        frame = np.array(frame)
        frame[self.y1:self.y2, self.x1:self.x2] = self.value
        return frame


class Rotate(FrameHandler):
    def __init__(self, angle: RotateAngle):
        self.angle = angle

    def handle(self, frame):
        return cv2.rotate(frame, self.angle.code)


class Gaussian(FrameHandler):
    def __init__(self, std=1, area=1):
        self.std = std
        self.area = area

    def handle(self, frame):
        frame = np.array(frame, dtype=float)
        if self.area >= 1:
            frame.flat += np.random.normal(0, self.std, frame.size)
        elif self.area > 0:
            amount = int(self.area * frame.size)
            flat_indices = np.random.choice(frame.size, amount, False)
            frame.flat[flat_indices] += np.random.normal(0, self.std, amount)
        return frame.clip(0, 255).astype(np.uint8)


class SaltAndPepper(FrameHandler):
    def __init__(self, area=1):
        self.area = area

    def handle(self, frame):
        frame = frame.copy()
        height, width = frame.shape[:2]
        total = height * width
        amount = int(self.area * total)

        flat_idx = np.random.choice(total, amount, False)
        flat_salt = flat_idx[:len(flat_idx) // 2]
        flat_pepper = flat_idx[len(flat_idx) // 2:]

        salt = np.unravel_index(flat_salt, (height, width))
        pepper = np.unravel_index(flat_pepper, (height, width))

        frame[salt] = 255
        frame[pepper] = 0

        return frame


def attack_video(
    attack,
    input_path,
    output_path,
    codec='mp4v',
    fps=None,
    height=None,
    width=None,
):
    with VideoTunnel(
        input_path,
        output_path,
        codec,
        fps,
        height,
        width
    ) as video_tunnel:
        video_tunnel.transfer_all(attack)


def name2class(name):
    return _ATTACKS.get(name)


_ATTACKS = {
    "flip": Flip,
    "resize": Resize,
    "crop": Crop,
    "fill": Fill,
    "rotate": Rotate,
    "gaussian": Gaussian,
    "salt-and-pepper": SaltAndPepper
}
