from abc import abstractmethod, ABC
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
from .transforms import frame2dwt_dct, frame2dwt_svd, frame2dwt_stack, WaveletSubband, Transformation, Pipe


class Algorithm(ABC):
    @property
    @abstractmethod
    def transformation(self) -> Transformation:
        pass

    @property
    @abstractmethod
    def method(self) -> Method:
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def embed(
        self,
        input_path: str,
        output_path: str,
        watermark_reader: WatermarkBitReader,
        codec: str = "mp4v"
    ) -> EmbeddingStatistics:
        embedding_suite = FrameEmbeddingSuite(self.transformation, self.method, watermark_reader)
        with WatermarkEmbedder(input_path, output_path, codec) as embedder:
            return embedder.embed(embedding_suite)

    def extract(
        self,
        input_path: str,
        watermark_writer: WatermarkBitWriter,
        quantity: int,
        preparer: Transformation = None
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


def name2class(name: str) -> Type[Algorithm]:
    return _ALGORITHMS.get(name)


_ALGORITHMS: Dict[str, Type[Algorithm]] = {
    "dwt-window-median": DwtWindowMedian,
    "dwt-dct-even-odd-differential": DwtDctEvenOddDifferential,
    "dwt-svd-mean-over-window-edges": DwtSvdMeanOverWindowEdges
}
