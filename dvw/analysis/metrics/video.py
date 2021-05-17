import cv2
import numpy as np
from skimage.metrics import structural_similarity

from .base import BaseMetric, MetricValue, Comparator
from dvw.core.io import PairVideoReader


def ssim(frame1, frame2):  # TODO: add typing
    return structural_similarity(frame1, frame2, multichannel=True)


class VideoMetric(BaseMetric):
    PSNR = ('psnr', 'Peak signal-to-noise ratio', cv2.PSNR, 'db')
    MSSIM = ('mssim', 'Mean structural similarity', ssim)


class VideoComparator(Comparator):
    def __init__(self, precision: int, *metrics: VideoMetric) -> None:
        super().__init__(precision)
        self.metrics = metrics or list(VideoMetric)

    def compare(self, path1: str, path2: str):  # TODO: add typing
        with PairVideoReader(path1, path2) as pair_video:
            return self._compare_frames(pair_video)

    def _compare_frames(self, pair_video: PairVideoReader):  # TODO: add typing
        cnt = 0
        total = np.zeros(len(self.metrics))

        success, frame1, frame2 = pair_video.read()
        while success:
            total += self._calculate_metrics(frame1, frame2)
            success, frame1, frame2 = pair_video.read()
            cnt += 1

        return self._calc_avg_metrics(total, cnt)

    def _calculate_metrics(self, frame1, frame2):  # TODO: add typing
        return [m.calculate(frame1, frame2) for m in self.metrics]

    def _calc_avg_metrics(self, total, cnt):  # TODO: add typing
        return [
            MetricValue(m, round(t / cnt, self.precision))
            for m, t in zip(self.metrics, total)
        ]
