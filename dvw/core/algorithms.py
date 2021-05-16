from abc import abstractmethod, ABC
from enum import Enum
from typing import Type, List, Dict

from .core import (
    WatermarkEmbedder,
    BlindWatermarkExtractor,
    FrameEmbeddingSuite,
    EmbeddingStatistics,
    ExtractingStatistics
)
from .io import VideoReader, WatermarkBitReader, WatermarkBitWriter
from .methods import (
    WindowMedian,
    EvenOddDifferential,
    MeanOverWindowEdges,
    WindowMedianBitManipulator,
    EvenOddDifferentialBitManipulator,
    MeanOverWindowEdgesBitManipulator,
    WindowPosition,
    Emphasis,
    Method
)
from .transforms import frame2dwt_dct, frame2dwt_svd, frame2dwt_stack, WaveletSubband, Transformation


class Algorithm(ABC):
    @property
    @abstractmethod
    def transformation(self) -> Transformation:
        pass

    @property
    @abstractmethod
    def method(self) -> Method:
        pass

    def embed(
        self,
        input_path: str,
        output_path: str,
        watermark_reader: WatermarkBitReader,
        codec: str = 'mp4v'
    ) -> EmbeddingStatistics:
        embedding_suite = FrameEmbeddingSuite(self.transformation, self.method, watermark_reader)
        with WatermarkEmbedder(input_path, output_path, codec) as embedder:
            return embedder.embed(embedding_suite)

    def extract(
        self,
        input_path: str,
        watermark_writer: WatermarkBitWriter,
        quantity: int
    ) -> ExtractingStatistics:
        extractor = BlindWatermarkExtractor(self.transformation, self.method)
        with VideoReader(input_path) as video_reader:
            return extractor.extract(video_reader, watermark_writer, quantity)


class DwtWindowMedian(Algorithm):
    def __init__(
        self,
        wavelet: str,
        level: int,
        subbands: List[WaveletSubband],
        position: WindowPosition,
        window_size: int,
        emphasis: Emphasis
    ):
        bit_manipulator = WindowMedianBitManipulator()
        submethod = emphasis.create(bit_manipulator)
        self._method = WindowMedian(window_size, submethod)
        self._transformation = frame2dwt_stack(wavelet, level, position, *subbands)

    @property
    def transformation(self) -> Transformation:
        return self._transformation

    @property
    def method(self) -> Method:
        return self._method


class DwtDctEvenOddDifferential(Algorithm):
    def __init__(
        self,
        wavelet: str,
        level: int,
        subbands: List[WaveletSubband],
        offset: float,
        area: float,
        repeats: int,
        alpha: float,
        emphasis: Emphasis
    ):
        bit_manipulator = EvenOddDifferentialBitManipulator(alpha)
        submethod = emphasis.create(bit_manipulator)
        self._method = EvenOddDifferential(offset, area, repeats, submethod)
        self._transformation = frame2dwt_dct(wavelet, level, *subbands)

    @property
    def transformation(self) -> Transformation:
        return self._transformation

    @property
    def method(self) -> Method:
        return self._method


class DwtSvdMeanOverWindowEdges(Algorithm):
    def __init__(
        self,
        wavelet: str,
        level: int,
        subbands: List[WaveletSubband],
        window_size: int,
        alpha: float,
        emphasis: Emphasis
    ):
        bit_manipulator = MeanOverWindowEdgesBitManipulator(alpha)
        submethod = emphasis.create(bit_manipulator)
        self._method = MeanOverWindowEdges(window_size, submethod)
        self._transformation = frame2dwt_svd(wavelet, level, *subbands)

    @property
    def transformation(self) -> Transformation:
        return self._transformation

    @property
    def method(self) -> Method:
        return self._method


# remove
def dwt_window_median(
    mode,
    wavelet,
    level,
    subbands,
    position,
    window_size,
    emphasis,
    **kwargs
):
    bit_manipulator = WindowMedianBitManipulator()
    submethod = emphasis.create(bit_manipulator)
    method = WindowMedian(window_size, submethod)
    transformation = frame2dwt_stack(wavelet, level, position, *subbands)
    return mode.run(transformation, method, **kwargs)


# remove
def dwt_dct_even_odd_differential(
    mode,
    wavelet,
    level,
    subbands,
    offset,
    area,
    repeats,
    alpha,
    emphasis,
    **kwargs
):
    bit_manipulator = EvenOddDifferentialBitManipulator(alpha)
    submethod = emphasis.create(bit_manipulator)
    method = EvenOddDifferential(offset, area, repeats, submethod)
    transformation = frame2dwt_dct(wavelet, level, *subbands)
    return mode.run(transformation, method, **kwargs)


# remove
def dwt_svd_mean_over_window_edges(
    mode,
    wavelet,
    level,
    subbands,
    window_size,
    alpha,
    emphasis,
    **kwargs
):
    bit_manipulator = MeanOverWindowEdgesBitManipulator(alpha)
    submethod = emphasis.create(bit_manipulator)
    method = MeanOverWindowEdges(window_size, submethod)
    transformation = frame2dwt_svd(wavelet, level, *subbands)
    return mode.run(transformation, method, **kwargs)


# remove
def _embed(
    transformation,
    method,
    watermark_path,
    watermark_type,
    input_path,
    output_path,
    **kwargs
):
    with watermark_type.reader(watermark_path, **kwargs) as watermark_reader, \
            WatermarkEmbedder(input_path, output_path) as embedder:
        embedding_suite = FrameEmbeddingSuite(transformation, method, watermark_reader)
        return embedder.embed(embedding_suite)


# remove
def _extract(
    transformation,
    method,
    watermark_path,
    watermark_type,
    input_path,
    quantity,
    **kwargs
):
    extractor = BlindWatermarkExtractor(transformation, method)
    with watermark_type.writer(watermark_path, **kwargs) as watermark_writer, \
            VideoReader(input_path) as video_reader:
        return extractor.extract(video_reader, watermark_writer, quantity)


# remove
class Mode(Enum):
    EMBED = ('embed', _embed)
    EXTRACT = ('extract', _extract)

    def __new__(cls, value, run_fn):
        obj = object().__new__(cls)
        obj._value_ = value
        obj.run = run_fn
        return obj


def name2class(name: str) -> Type[Algorithm]:
    return _ALGORITHMS.get(name)


_ALGORITHMS: Dict[str, Type[Algorithm]] = {
    "dwt-window-median": DwtWindowMedian,
    "dwt-dct-even-odd-differential": DwtDctEvenOddDifferential,
    "dwt-svd-mean-over-window-edges": DwtSvdMeanOverWindowEdges
}
