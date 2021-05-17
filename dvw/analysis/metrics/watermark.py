from typing import Any

import numpy as np

from .base import BaseMetric, MetricValue, Comparator
from ...core.io import WatermarkType


def _ber(watermark_reader1, watermark_reader2, precision):  # TODO: add typing
    errors = 0
    total = 0

    while watermark_reader1.available() and watermark_reader2.available():
        bit1 = watermark_reader1.read_bit()
        bit2 = watermark_reader2.read_bit()
        errors += (bit1 != bit2)
        total += 1

    ber_ = 100 * ((errors / total) if total else 1)
    ber_ = round(ber_, precision)
    values = [('Total', total), ('Errors', errors), ('BER', ber_)]
    return MetricValue(WatermarkMetric.BER, values)


def _normalized_correlation(watermark_reader1, watermark_reader2, precision):  # TODO: add typing
    a = watermark_reader1.read_all()
    b = watermark_reader2.read_all()

    a = (a - np.mean(a)) / (np.std(a) * len(a))
    b = (b - np.mean(b)) / (np.std(b))

    nc = round(np.correlate(a, b)[0], precision)
    return MetricValue(WatermarkMetric.NC, nc)


class WatermarkMetric(BaseMetric):
    BER = ('ber', 'Bit error rate', _ber, '%')
    NC = ('nc', 'Normalized correlation', _normalized_correlation)


class WatermarkComparator(Comparator):
    def __init__(self, precision: int, *metrics: WatermarkMetric) -> None:
        super().__init__(precision)
        self.metrics = metrics or list(WatermarkMetric)

    def compare(
        self,
        path1: str,
        path2: str,
        watermark_type: WatermarkType,
        **kwargs: Any
    ):  # TODO: add typing
        return [
            self._calculate_metric(path1, path2, watermark_type, m, **kwargs)
            for m in self.metrics
        ]

    def _calculate_metric(
        self,
        path1: str,
        path2: str,
        watermark_type: WatermarkType,
        metric: WatermarkMetric,
        **kwargs: Any
    ):  # TODO: add typing
        with watermark_type.reader(path1, **kwargs) as watermark_reader1, \
                watermark_type.reader(path2, **kwargs) as watermark_reader2:
            return metric.calculate(watermark_reader1, watermark_reader2, self.precision)
