from dataclasses import dataclass
from enum import IntEnum
from time import time
from typing import Dict, Any, Tuple

import numpy as np

from .io import VideoTunnel, WatermarkBitReader, WatermarkBitWriter
from .io.video import FrameHandler, VideoReader
from .methods import Method
from .transforms import Transformation
from .util.base import Observable, CloneableDataclass, PrettyDictionary


class EmbedEvent(IntEnum):
    BEFORE_EMBEDDING = 1
    AFTER_EMBEDDING = 2
    BEFORE_FRAME_EMBEDDING = 3
    AFTER_FRAME_EMBEDDING = 4
    ERROR_EMBEDDING = 5


@dataclass
class EmbeddingStatistics(CloneableDataclass, PrettyDictionary):
    total_frames: int
    embedded: int = 0
    copied: int = 0
    full_watermark: bool = False
    start_time: float = 0
    end_time: float = 0

    @property
    def frames_with_watermark(self) -> int:
        return self.total_frames - self.copied

    @property
    def elapsed_time(self) -> float:
        return self.end_time - self.start_time

    def dictionary(self) -> Dict[str, Any]:
        return {
            "Total frames": self.total_frames,
            "Embedded bits": self.embedded,
            "Copied frames": self.copied,
            "Frames with watermark": self.frames_with_watermark,
            "Full watermark": self.full_watermark,
            "Start time": self.start_time,
            "End time": self.end_time,
            "Elapsed time": self.elapsed_time,
        }


class FrameEmbeddingKit(FrameHandler):
    def __init__(
        self,
        transformation: Transformation,
        method: Method,
        watermark_reader: WatermarkBitReader,
    ) -> None:
        self.transformation = transformation
        self.method = method
        self.watermark_reader = watermark_reader

    def workable(self) -> bool:
        return self.watermark_reader.available()

    def handle(self, frame: np.ndarray) -> Tuple[np.ndarray, int]:
        memory = []
        domain = self.transformation.transform(frame, memory)
        watermarked_domain, embedded = self.method.embed(domain, self.watermark_reader)
        return self.transformation.restore(watermarked_domain, memory), embedded


class WatermarkEmbedder(VideoTunnel):
    def __init__(self, input_path: str, output_path: str, codec: str = "mp4v") -> None:
        super().__init__(input_path, output_path, codec)
        self.statistics = EmbeddingStatistics(self.frames)

    def embed(
        self, embedding_kit: FrameEmbeddingKit, copy: bool = True
    ) -> EmbeddingStatistics:
        try:
            return self._embed(embedding_kit, copy)
        except Exception as e:
            self.notify(EmbedEvent.ERROR_EMBEDDING, exception=e)
            raise

    def _embed(
        self, embedding_kit: FrameEmbeddingKit, copy: bool
    ) -> EmbeddingStatistics:
        self.notify(EmbedEvent.AFTER_EMBEDDING)
        self.statistics.start_time = time()

        if not embedding_kit.workable():
            if copy:
                self.statistics.copied = self.copy_frames()
            return self.statistics

        success = True
        while success and embedding_kit.workable():
            self._notify_embedding(EmbedEvent.BEFORE_FRAME_EMBEDDING)
            success, *result = self.transfer(embedding_kit)
            self.statistics.embedded += success and result[1]
            self._notify_embedding(EmbedEvent.AFTER_FRAME_EMBEDDING)

        if copy:
            self.statistics.copied = self.copy_frames()

        self.statistics.end_time = time()
        self.statistics.full_watermark = not embedding_kit.workable()

        self.notify(
            EmbedEvent.AFTER_EMBEDDING, statistics=self.statistics.shallow_copy()
        )
        return self.statistics

    def _notify_embedding(self, event: Any) -> None:
        self.notify(
            event,
            position=self.position,
            total=self.frames,
            embedded=self.statistics.embedded,
        )


class ExtractEvent(IntEnum):
    BEFORE_EXTRACTING = 1
    AFTER_EXTRACTING = 2
    BEFORE_FRAME_EXTRACTING = 3
    AFTER_FRAME_EXTRACTING = 4
    ERROR_EXTRACTING = 5


@dataclass
class ExtractingStatistics(CloneableDataclass, PrettyDictionary):
    left: int
    extracted: int = 0
    start_time: float = 0
    end_time: float = 0

    @property
    def total(self) -> int:
        return self.left + self.extracted

    @property
    def elapsed_time(self) -> float:
        return self.end_time - self.start_time

    @property
    def full_watermark(self) -> bool:
        return not self.left

    def dictionary(self) -> Dict[str, Any]:
        return {
            "Total bits": self.total,
            "Left bits": self.left,
            "Extracted bits": self.extracted,
            "Full watermark": self.full_watermark,
            "Start time": self.start_time,
            "End time": self.end_time,
            "Elapsed time": self.elapsed_time,
        }


class BlindWatermarkExtractor(Observable):
    def __init__(self, transformation: Transformation, method: Method) -> None:
        super().__init__()
        self.transformation = transformation
        self.method = method

    def extract(
        self,
        video_reader: VideoReader,
        watermark_writer: WatermarkBitWriter,
        quantity: int,
    ) -> ExtractingStatistics:
        try:
            return self._stream2watermark(video_reader, watermark_writer, quantity)
        except Exception as e:
            self.notify(ExtractEvent.ERROR_EXTRACTING, exception=e)
            raise

    def _stream2watermark(
        self,
        video_reader: VideoReader,
        watermark_writer: WatermarkBitWriter,
        quantity: int,
    ) -> ExtractingStatistics:
        self.notify(ExtractEvent.BEFORE_EXTRACTING)

        statistics = ExtractingStatistics(quantity)
        statistics.start_time = time()

        success, frame = video_reader.read()
        while success and statistics.left > 0:
            self._notify_extracting(ExtractEvent.BEFORE_FRAME_EXTRACTING, statistics)
            amount = self._frame2watermark(frame, watermark_writer, statistics.left)
            statistics.extracted += amount
            statistics.left -= amount
            self._notify_extracting(ExtractEvent.AFTER_FRAME_EXTRACTING, statistics)
            success, frame = video_reader.read()

        statistics.end_time = time()
        self.notify(ExtractEvent.AFTER_EXTRACTING, statistics=statistics.shallow_copy())

        return statistics

    def _frame2watermark(
        self, frame: np.ndarray, watermark_writer: WatermarkBitWriter, quantity: int
    ) -> int:
        domain = self.transformation.transform(frame, [])
        return self.method.extract(domain, watermark_writer, quantity)

    def _notify_extracting(self, event: Any, statistics: ExtractingStatistics) -> None:
        self.notify(event, total=statistics.total, position=statistics.extracted)
