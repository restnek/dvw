from abc import ABC
from typing import Type, Dict, Iterable, Optional

from dvw.core import (
    WatermarkEmbedder,
    BlindWatermarkExtractor,
    FrameEmbeddingKit,
    EmbeddingStatistics,
    ExtractingStatistics,
)
from dvw.core.methods import (
    WindowMedian,
    EvenOddDifferential,
    MeanOverWindowEdges,
    WindowMedianBitManipulator,
    EvenOddDifferentialBitManipulator,
    MeanOverWindowEdgesBitManipulator,
    WindowPosition,
    Emphasis,
    Method,
)
from dvw.core.transforms import (
    frame2dwt_dct,
    frame2dwt_svd,
    frame2dwt_stack,
    WaveletSubband,
    Transformation,
    Pipe,
)
from dvw.io.video import VideoReader
from dvw.io.watermark import WatermarkBitReader, WatermarkBitWriter


class Algorithm(ABC):
    def __init__(self, transformation: Transformation, method: Method) -> None:
        self.transformation = transformation
        self.method = method

    def embed(
        self,
        input_path: str,
        output_path: str,
        watermark_reader: WatermarkBitReader,
        codec: str = "mp4v",
    ) -> EmbeddingStatistics:
        embedding_suite = FrameEmbeddingKit(
            self.transformation, self.method, watermark_reader
        )
        with WatermarkEmbedder(input_path, output_path, codec) as embedder:
            return embedder.embed(embedding_suite)

    def extract(
        self,
        input_path: str,
        watermark_writer: WatermarkBitWriter,
        quantity: int,
        preparer: Optional[Transformation] = None,
    ) -> ExtractingStatistics:
        transformation = self.transformation
        if preparer:
            transformation = Pipe(preparer, transformation)

        extractor = BlindWatermarkExtractor(transformation, self.method)
        with VideoReader(input_path) as video_reader:
            return extractor.extract(video_reader, watermark_writer, quantity)


class DwtWindowMedian(Algorithm):
    def __init__(
        self,
        wavelet: str,
        level: int,
        subbands: Iterable[WaveletSubband],
        position: WindowPosition,
        window_size: int,
        emphasis: Emphasis,
    ):
        bit_manipulator = WindowMedianBitManipulator()
        submethod = emphasis.create(bit_manipulator)
        method = WindowMedian(window_size, submethod)
        transformation = frame2dwt_stack(wavelet, level, position, *subbands)
        super().__init__(transformation, method)


class DwtDctEvenOddDifferential(Algorithm):
    def __init__(
        self,
        wavelet: str,
        level: int,
        subbands: Iterable[WaveletSubband],
        offset: float,
        area: float,
        repeats: int,
        alpha: float,
        emphasis: Emphasis,
    ):
        bit_manipulator = EvenOddDifferentialBitManipulator(alpha)
        submethod = emphasis.create(bit_manipulator)
        method = EvenOddDifferential(offset, area, repeats, submethod)
        transformation = frame2dwt_dct(wavelet, level, *subbands)
        super().__init__(transformation, method)


class DwtSvdMeanOverWindowEdges(Algorithm):
    def __init__(
        self,
        wavelet: str,
        level: int,
        subbands: Iterable[WaveletSubband],
        window_size: int,
        alpha: float,
        emphasis: Emphasis,
    ):
        bit_manipulator = MeanOverWindowEdgesBitManipulator(alpha)
        submethod = emphasis.create(bit_manipulator)
        method = MeanOverWindowEdges(window_size, submethod)
        transformation = frame2dwt_svd(wavelet, level, *subbands)
        super().__init__(transformation, method)


def name2class(name: str) -> Type[Algorithm]:
    return _ALGORITHMS.get(name)


_ALGORITHMS: Dict[str, Type[Algorithm]] = {
    "dwt-window-median": DwtWindowMedian,
    "dwt-dct-even-odd-differential": DwtDctEvenOddDifferential,
    "dwt-svd-mean-over-window-edges": DwtSvdMeanOverWindowEdges,
}
