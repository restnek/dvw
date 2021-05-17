from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Tuple, Optional, Any

import cv2
import numpy as np

from ..util import shape2shape, istuple
from ..util.base import AutoCloseable, Observable


class VideoReader(AutoCloseable):
    def __init__(self, path: str) -> None:
        self.video = cv2.VideoCapture(path)

    def close(self) -> None:
        self.video.release()

    @property
    def fps(self) -> int:
        return int(self.video.get(cv2.CAP_PROP_FPS))

    @property
    def width(self) -> int:
        return int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self) -> int:
        return int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def shape(self) -> Tuple[int, int]:
        return self.height, self.width

    @property
    def frames(self) -> int:
        return int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))

    @property
    def position(self) -> int:
        return int(self.video.get(cv2.CAP_PROP_POS_FRAMES))

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        return self.video.read()


class PairVideoReader(AutoCloseable):
    def __init__(self, path1: str, path2: str):
        self.video1 = cv2.VideoCapture(path1)
        self.video2 = cv2.VideoCapture(path2)

    def close(self) -> None:
        self.video1.release()
        self.video2.release()

    def read(self) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
        success1, frame1 = self.video1.read()
        success2, frame2 = self.video2.read()
        return success1 and success2, frame1, frame2


class VideoTunnelEvent(Enum):
    BEFORE_FRAME_COPY = auto()
    AFTER_FRAME_COPY = auto()


class FrameHandler(ABC):
    @abstractmethod
    def handle(self, frame):  # TODO: add typing
        pass


class VideoTunnel(AutoCloseable, Observable):
    def __init__(
        self,
        input_path: str,
        output_path: str,
        codec: str,
        fps: Optional[int] = None,
        shape=None  # TODO: add typing
    ):
        super().__init__()
        self.reader = VideoReader(input_path)
        self.writer = cv2.VideoWriter(
            output_path,
            codec_code(codec),
            fps or self.reader.fps,
            shape2shape(self.reader.shape, shape)[::-1])

    def close(self) -> None:
        self.reader.close()
        self.writer.release()

    @property
    def frames(self) -> int:
        return self.reader.frames

    @property
    def position(self) -> int:
        return self.reader.position

    def transfer_all(self, frame_handler: FrameHandler) -> None:
        while self.transfer(frame_handler)[0]:
            pass

    def transfer(self, frame_handler: FrameHandler):  # TODO: add typing
        success, frame = self.reader.read()
        if success:
            result = frame_handler.handle(frame)
            frame = result[0] if istuple(result) else result
            self.writer.write(frame)
            return success, *result
        return success, None

    def copy_frames(self) -> int:
        copied = 0
        success, frame = self.reader.read()
        while success:
            self._notify_copy(VideoTunnelEvent.BEFORE_FRAME_COPY, copied)
            self.writer.write(frame)
            copied += 1
            self._notify_copy(VideoTunnelEvent.AFTER_FRAME_COPY, copied)
            success, frame = self.reader.read()
        return copied

    def _notify_copy(self, event: Any, copied: int) -> None:
        self.notify(
            event,
            position=self.position,
            total=self.frames,
            copied=copied)


def codec_code(codec: str) -> int:
    return cv2.VideoWriter_fourcc(*codec)
