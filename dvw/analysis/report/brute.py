from typing import List, Tuple, Optional

from .config import AnalysisKit, AnalysisHolder, WatermarkHolder
from .report import Report
from ..attacks.attacks import Attack
from ..metrics import WatermarkMetric, MetricValue
from ..metrics.video import VideoComparator, VideoMetric
from ...core.algorithms import Algorithm
from ...core.core import ExtractingStatistics, EmbeddingStatistics


class BruteForce:
    def __init__(self, kit: AnalysisKit, precision: int) -> None:
        self.kit = kit
        self.precision = precision

    def start(self, report: Report) -> None:
        for k in self.kit:
            self._brute_algorithms(k, report)

    def _brute_algorithms(self, analysis_holder: AnalysisHolder, report: Report) -> None:
        for algorithm in analysis_holder.algorithm:
            watermarked_video = report.resolve_path(analysis_holder.video, algorithm.name)
            embedding_result = self._embed(
                analysis_holder.video,
                watermarked_video,
                analysis_holder.watermark,
                algorithm,
                analysis_holder.video_metrics
            )
            report.add_embedding_result(*embedding_result)

            quantity = embedding_result[0].embedded
            restored_watermark = report.resolve_path(
                analysis_holder.watermark.path,
                algorithm.name)
            extracting_result = self._extract(
                watermarked_video,
                restored_watermark,
                analysis_holder.watermark,
                algorithm,
                quantity,
                analysis_holder.watermark_metrics)
            report.add_extracting_result(*extracting_result)

            # self._brute_attacks(analysis_holder, watermarked_video, algorithm, quantity, report)

    def _embed(
        self,
        input_path: str,
        output_path: str,
        watermark_holder: WatermarkHolder,
        algorithm: Algorithm,
        video_metrics: List[VideoMetric]
    ) -> Tuple[EmbeddingStatistics, Optional[List[MetricValue]]]:
        with watermark_holder.reader() as watermark_reader:
            statistics = algorithm.embed(input_path, output_path, watermark_reader)

        metric_values = None
        if video_metrics:
            comparator = VideoComparator(self.precision, *video_metrics)
            metric_values = comparator.compare(input_path, output_path)

        return statistics, metric_values

    def _extract(
        self,
        input_path: str,
        output_path: str,
        watermark_holder: WatermarkHolder,
        algorithm: Algorithm,
        quantity: int,
        watermark_metrics: List[WatermarkMetric],
        attack: Attack = None
    ) -> Tuple[ExtractingStatistics, Optional[List[MetricValue]]]:
        with watermark_holder.writer(output_path) as watermark_writer:
            statistics = algorithm.extract(input_path, watermark_writer, quantity, attack)

        metric_values = None
        if watermark_metrics:
            metric_values = watermark_holder.compare(
                output_path,
                self.precision,
                watermark_metrics)

        return statistics, metric_values

    def _brute_attacks(
        self,
        analysis_holder: AnalysisHolder,
        watermarked_video: str,
        algorithm: Algorithm,
        quantity: int,
        report: Report
    ) -> None:
        for attack_holder in analysis_holder.attacks:
            for attack in attack_holder:
                restored_watermark = report.resolve_path(
                    analysis_holder.watermark.path,
                    algorithm.name)  # remake
                extracting_result = self._extract(
                    watermarked_video,
                    restored_watermark,
                    analysis_holder.watermark,
                    algorithm,
                    quantity,
                    analysis_holder.watermark_metrics,
                    attack)
                report.add_attack_result(*extracting_result)
