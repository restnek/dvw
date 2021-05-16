from pprint import pprint

from .config import AnalysisKit
from ..metrics.video import VideoComparator
from ..metrics.watermark import WatermarkComparator


class BruteForce:
    def __init__(self, kit: AnalysisKit):
        self.kit = kit

    def start(self):
        for k in self.kit:
            self._brute_algorithms(*k)

    def _brute_algorithms(
        self,
        video,
        watermark,
        algorithm,
        attack,
        video_metrics,
        watermark_metrics
    ):
        precision = 7
        for a in algorithm:
            with watermark.reader() as watermark_reader:
                embedding_result = a.embed(video, "test.mp4", watermark_reader)

            video_metric_result = None
            if video_metrics:
                video_comparator = VideoComparator(precision, *video_metrics)
                video_metric_result = video_comparator.compare(video, "test.mp4")
            pprint(embedding_result)
            pprint(video_metric_result)

            with watermark.writer("watermark.png") as watermark_writer:
                extracting_result = a.extract("test.mp4", watermark_writer, 39900)

            watermark_metric_result = None
            if watermark_metrics:
                watermark_metric_result = watermark.compare(
                    "watermark.png",
                    precision,
                    watermark_metrics)
            pprint(extracting_result)
            pprint(watermark_metric_result)
