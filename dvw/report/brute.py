from itertools import product
from typing import List, Tuple, Optional

from dvw.attacks import Attack
from dvw.core import ExtractingStatistics, EmbeddingStatistics
from dvw.core.algorithms import Algorithm
from dvw.metrics.base import MetricValue
from dvw.metrics.video import VideoComparator
from dvw.report import Report
from dvw.report.config import AnalysisKit, WatermarkHolder, ClassHolder


class BruteForce:
    def __init__(self, kit: AnalysisKit, precision: int) -> None:
        self.kit = kit
        self.precision = precision

    def start(self, report: Report) -> None:
        report.add_sources(self.kit.videos, self.kit.watermarks)
        for a in self.kit.algorithms:
            report.new_algorithm(a.class_.__name__)
            self._brute_algorithms(a, report)

    def _brute_algorithms(self, algorithm_holder: ClassHolder, report: Report) -> None:
        for a, params in algorithm_holder:
            report.new_experiment(params)
            self._brute_assets(a, report)

    def _brute_assets(self, algorithm: Algorithm, report: Report) -> None:
        for v, w in product(self.kit.videos, self.kit.watermarks):
            report.new_assets()

            watermarked_video = report.resolve_path(v)
            embedding_result = self._embed(v, watermarked_video, w, algorithm)

            quantity = embedding_result[0].embedded
            restored_watermark = report.resolve_path(w.path)
            extracting_result = self._extract(
                watermarked_video, restored_watermark, w, algorithm, quantity
            )

            report.add_statistics(*embedding_result, *extracting_result)

            self._brute_attacks(watermarked_video, w, algorithm, report, quantity)

    def _brute_attacks(
        self,
        watermarked_video: str,
        watermark: WatermarkHolder,
        algorithm: Algorithm,
        report: Report,
        quantity: int,
    ) -> None:
        for attack_holder in self.kit.attacks:
            report.new_attack(attack_holder.class_.__name__)
            for a, params in attack_holder:
                restored_watermark = report.resolve_path(watermark.path)
                extracting_result = self._extract(
                    watermarked_video,
                    restored_watermark,
                    watermark,
                    algorithm,
                    quantity,
                    a,
                )
                report.add_attack_statistics(*extracting_result, params)

    def _embed(
        self,
        input_path: str,
        output_path: str,
        watermark_holder: WatermarkHolder,
        algorithm: Algorithm,
    ) -> Tuple[EmbeddingStatistics, Optional[List[MetricValue]]]:
        with watermark_holder.reader() as watermark_reader:
            statistics = algorithm.embed(input_path, output_path, watermark_reader)

        metric_values = None
        if self.kit.video_metrics:
            comparator = VideoComparator(self.precision, *self.kit.video_metrics)
            metric_values = comparator.compare(input_path, output_path)

        return statistics, metric_values

    def _extract(
        self,
        input_path: str,
        output_path: str,
        watermark_holder: WatermarkHolder,
        algorithm: Algorithm,
        quantity: int,
        attack: Optional[Attack] = None,
    ) -> Tuple[ExtractingStatistics, Optional[List[MetricValue]]]:
        with watermark_holder.writer(output_path) as watermark_writer:
            statistics = algorithm.extract(
                input_path, watermark_writer, quantity, attack
            )

        metric_values = None
        if self.kit.watermark_metrics:
            metric_values = watermark_holder.compare(
                output_path, self.precision, self.kit.watermark_metrics
            )

        return statistics, metric_values
