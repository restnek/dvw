from typing import List, Iterable, Tuple, Callable

import cv2
import numpy as np
from skimage.metrics import structural_similarity

from dvw.io.video import PairVideoReader
from dvw.metrics.base import BaseMetric, MetricValue, Comparator


def ssim(frame1: np.ndarray, frame2: np.ndarray) -> float:
    return structural_similarity(frame1, frame2, multichannel=True)


class VideoMetric(BaseMetric):
    PSNR = ("psnr", "Peak signal-to-noise ratio", cv2.PSNR, "db")
    MSSIM = ("mssim", "Mean structural similarity", ssim)


class VideoComparator(Comparator):
    def __init__(self, precision: int, *metrics: VideoMetric) -> None:
        super().__init__(precision)
        self.metrics = metrics or list(VideoMetric)

    def compare(self, path1: str, path2: str) -> List[MetricValue]:
        with PairVideoReader(path1, path2) as pair_video:
            return self._compare_frames(pair_video)

    def _compare_frames(self, pair_video: PairVideoReader) -> List[MetricValue]:
        cnt = 0
        min_ = None
        max_ = None
        total = np.zeros(len(self.metrics))

        success, frame1, frame2 = pair_video.read()
        while success:
            values = self._calculate_metrics(frame1, frame2)
            min_ = self._update_statistics(values, min_, min) if min_ else values
            max_ = self._update_statistics(values, max_, max) if max_ else values
            total += values
            success, frame1, frame2 = pair_video.read()
            cnt += 1

        metric_values = self._calc_avg_metrics(total, cnt)
        self._add_statistics(metric_values, [("Min", min_), ("Max", max_)])
        return metric_values

    def _calculate_metrics(self, frame1: np.ndarray, frame2: np.ndarray) -> List[float]:
        return [m.calculate(frame1, frame2) for m in self.metrics]

    def _update_statistics(
        self,
        metric_values: List[float],
        statistics: List[float],
        fn: Callable[[Tuple[float, float]], float],
    ) -> List[float]:
        return list(map(fn, zip(metric_values, statistics)))

    def _calc_avg_metrics(self, total: np.ndarray, cnt: int) -> List[MetricValue]:
        return [
            MetricValue(m, round(t / cnt, self.precision))
            for m, t in zip(self.metrics, total)
        ]

    def _add_statistics(
        self,
        metric_values: List[MetricValue],
        data: List[Tuple[str, Iterable[float]]],
    ) -> None:
        statistics = [{} for _ in range(len(metric_values))]

        for k, v in data:
            for i, x in enumerate(v):
                statistics[i][k] = x

        for m, s in zip(metric_values, statistics):
            m.statistics = s
