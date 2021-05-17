from dataclasses import dataclass
from enum import Enum, auto
from time import time

from .io import VideoTunnel
from .io.video import FrameHandler
from .util.base import Observable, CloneableDataclass


class EmbedEvent(Enum):
    BEFORE_EMBEDDING = auto()
    AFTER_EMBEDDING = auto()
    BEFORE_FRAME_EMBEDDING = auto()
    AFTER_FRAME_EMBEDDING = auto()
    ERROR_EMBEDDING = auto()


@dataclass
class EmbeddingStatistics(CloneableDataclass):
    total_frames: int
    embedded: int = 0
    copied: int = 0
    full_watermark: bool = False
    start_time: float = 0
    end_time: float = 0

    @property
    def frames_with_watermark(self):
        return self.total_frames - self.copied

    @property
    def elapsed_time(self):
        return self.end_time - self.start_time


class FrameEmbeddingSuite(FrameHandler):
    def __init__(self, transformation, method, watermark_reader):
        self.transformation = transformation
        self.method = method
        self.watermark_reader = watermark_reader

    def workable(self):
        return self.watermark_reader.available()

    def handle(self, frame):
        memory = []
        domain = self.transformation.transform(frame, memory)
        watermarked_domain, embedded = self.method.embed(domain, self.watermark_reader)
        return self.transformation.restore(watermarked_domain, memory), embedded


class WatermarkEmbedder(VideoTunnel):
    def __init__(self, input_path, output_path, codec="mp4v"):
        super().__init__(input_path, output_path, codec)
        self.statistics = EmbeddingStatistics(self.frames)

    def embed(self, embedding_suite, copy=True):
        try:
            return self._embed(embedding_suite, copy)
        except Exception as e:
            self.notify(EmbedEvent.ERROR_EMBEDDING, exception=e)
            raise

    def _embed(self, embedding_suite, copy):
        self.notify(EmbedEvent.AFTER_EMBEDDING)
        self.statistics.start_time = time()

        if not embedding_suite.workable():
            if copy:
                self.statistics.copied = self.copy_frames()
            return self.statistics

        success = True
        while success and embedding_suite.workable():
            self._notify_embedding(EmbedEvent.BEFORE_FRAME_EMBEDDING)
            success, *result = self.transfer(embedding_suite)
            self.statistics.embedded += success and result[1]
            self._notify_embedding(EmbedEvent.AFTER_FRAME_EMBEDDING)

        if copy:
            self.statistics.copied = self.copy_frames()

        self.statistics.end_time = time()
        self.statistics.full_watermark = not embedding_suite.workable()

        self.notify(
            EmbedEvent.AFTER_EMBEDDING, statistics=self.statistics.shallow_copy()
        )
        return self.statistics

    def _notify_embedding(self, event):
        self.notify(
            event,
            position=self.position,
            total=self.frames,
            embedded=self.statistics.embedded,
        )


class ExtractEvent(Enum):
    BEFORE_EXTRACTING = auto()
    AFTER_EXTRACTING = auto()
    BEFORE_FRAME_EXTRACTING = auto()
    AFTER_FRAME_EXTRACTING = auto()
    ERROR_EXTRACTING = auto()


@dataclass
class ExtractingStatistics(CloneableDataclass):
    left: int
    extracted: int = 0
    start_time: float = 0
    end_time: float = 0

    @property
    def total(self):
        return self.left + self.extracted

    @property
    def elapsed_time(self):
        return self.end_time - self.start_time

    @property
    def full_watermark(self):
        return not self.left


class BlindWatermarkExtractor(Observable):
    def __init__(self, transformation, method):
        super().__init__()
        self.transformation = transformation
        self.method = method

    def extract(self, video_reader, watermark_writer, quantity):
        try:
            return self._stream2watermark(video_reader, watermark_writer, quantity)
        except Exception as e:
            self.notify(ExtractEvent.ERROR_EXTRACTING, exception=e)
            raise

    def _stream2watermark(self, video_reader, watermark_writer, quantity):
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

    def _frame2watermark(self, frame, watermark_writer, quantity):
        domain = self.transformation.transform(frame, [])
        return self.method.extract(domain, watermark_writer, quantity)

    def _notify_extracting(self, event, statistics):
        self.notify(event, total=statistics.total, position=statistics.extracted)
