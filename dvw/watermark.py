import cv2

from .io import create_reader, create_writer
from .media import copy_caption, copy_frames
from .methods import WindowMedian
from .transformations import frame2wavelet


class WatermarkEmbedder:
    def __init__(self, transformation, method):
        self.transformation = transformation
        self.method = method

    def embed(self, video_path, wmvideo_path, wmreader, codec='mp4v'):
        video_caption, wmvideo_writer = copy_caption(
            video_path,
            wmvideo_path,
            codec)

        embedded = self._embed2stream(
            video_caption,
            wmvideo_writer,
            wmreader)

        video_caption.release()
        wmvideo_writer.release()

        return embedded

    def _embed2stream(self, video_capture, wmvideo_writer, wmreader):
        embedded = 0

        if not wmreader.available():
            copy_frames(video_capture, wmvideo_writer)
            return embedded

        success, frame = video_capture.read()
        while success:
            wmframe, amount = self._embed2frame(frame, wmreader)
            wmvideo_writer.write(wmframe)
            embedded += amount
            if not wmreader.available():
                break
            success, frame = video_capture.read()

        copy_frames(video_capture, wmvideo_writer)
        return embedded

    def _embed2frame(self, frame, wmreader):
        domain = self.transformation.transform(frame)
        wmdomain, embedded = self.method.embed(domain, wmreader)
        return self.transformation.restore(wmdomain), embedded


class BlindWatermarkExtractor:
    def __init__(self, transformation, method):
        self.transformation = transformation
        self.method = method

    def extract(self, wmvideo_path, wmwriter, quantity):
        wmvideo_capture = cv2.VideoCapture(wmvideo_path)
        self._stream2wm(wmvideo_capture, wmwriter, quantity)
        wmvideo_capture.release()

    def _stream2wm(self, wmvideo_capture, wmwriter, quantity):
        success, wmframe = wmvideo_capture.read()
        while success and quantity > 0:
            wmdomain = self.transformation.transform(wmframe)
            extracted = self.method.extract(wmdomain, wmwriter, quantity)
            quantity -= extracted
            success, wmframe = wmvideo_capture.read()


def embed(algorithm, wmpath, wmtype, video_path, wmvideo_path, **kwargs):
    embedder = _ALGORITHMS[algorithm][0](True, **kwargs)
    with create_reader(wmpath, wmtype, **kwargs) as wmreader:
        return embedder.embed(video_path, wmvideo_path, wmreader)


def extract(algorithm, wmpath, wmtype, wmvideo_path, quantity, **kwargs):
    extractor = _ALGORITHMS[algorithm][0](False, **kwargs)
    with create_writer(wmpath, wmtype, **kwargs) as wmwriter:
        extractor.extract(wmvideo_path, wmwriter, quantity)


def _dwt_window_median(extract_mode, wavelet=None, level=None, **kwargs):
    method = WindowMedian()
    transformation = frame2wavelet(wavelet, level)
    if extract_mode:
        return WatermarkEmbedder(transformation, method)
    return BlindWatermarkExtractor(transformation, method)


def algorithms():
    return dict.keys(_ALGORITHMS)


def algorithm_options(algorithm):
    return _ALGORITHMS[algorithm][1].copy()


_ALGORITHMS = {
    'dwt-window-median': [
        _dwt_window_median,
        {'level': int, 'wavelet': str}
    ]
}
