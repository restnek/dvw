import dataclasses
import os.path
import shutil
from abc import ABC
from typing import Iterable, Any, Dict, Optional

from dvw.core import ExtractingStatistics, EmbeddingStatistics
from dvw.metrics.base import MetricValue
from dvw.report.config import WatermarkHolder
from dvw.util import create_folder
from dvw.util.util import save_json, filename


class ResourceWatcher(ABC):
    def __init__(
        self, path: str, subwatcher: Optional["ResourceWatcher"] = None
    ) -> None:
        self.path = path
        self.subwatcher = subwatcher

    def resolve_path(self, path: str) -> str:
        if self.subwatcher:
            return self.subwatcher.resolve_path(path)
        return os.path.join(self.path, filename(path))

    def add_assets(self) -> None:
        self.subwatcher.add_assets()

    def add_attack(self, attack: str) -> None:
        self.subwatcher.add_attack(attack)

    def add_assets_statistics(
        self,
        video_path: str,
        watermark_path: str,
        embedding_statistics: EmbeddingStatistics,
        video_metrics: Optional[Iterable[MetricValue]],
        extracting_statistics: ExtractingStatistics,
        watermark_metrics: Optional[Iterable[MetricValue]],
    ) -> None:
        self.subwatcher.add_assets_statistics(
            video_path,
            watermark_path,
            embedding_statistics,
            video_metrics,
            extracting_statistics,
            watermark_metrics,
        )

    def add_attack_statistics(
        self,
        watermark_path: str,
        params: Dict[str, Any],
        extracting_statistics: ExtractingStatistics,
        watermark_metrics: Optional[Iterable[MetricValue]],
    ) -> None:
        self.subwatcher.add_attack_statistics(
            watermark_path, params, extracting_statistics, watermark_metrics
        )


class AlgorithmWatcher(ResourceWatcher):
    def __init__(
        self,
        path: str,
        experiment_folder: str,
        assets_folder: str,
        result_filename: str,
    ) -> None:
        path = create_folder(path)
        super().__init__(path)

        self.experiment_folder = experiment_folder
        self.assets_folder = assets_folder
        self.result_filename = result_filename
        self.experiment_id = 0

    def add_experiment(self, params: Dict[str, Any]) -> str:
        self.experiment_id += 1
        experiment_folder = self.experiment_folder + str(self.experiment_id)
        experiment_path = os.path.join(self.path, experiment_folder)
        self.subwatcher = ExperimentWatcher(
            experiment_path,
            params,
            self.assets_folder,
            self.result_filename,
        )
        return experiment_folder


class ExperimentWatcher(ResourceWatcher):
    def __init__(
        self,
        path: str,
        params: Dict[str, Any],
        assets_folder: str,
        result_filename: str,
    ) -> None:
        path = create_folder(path)
        super().__init__(path)

        self.data: Dict[str, Any] = {"params": params}
        self.assets_folder = assets_folder
        self.result_filename = result_filename
        self.result_path = os.path.join(path, result_filename)
        self.assets_id = 0
        save_json(self.result_filename, self.data)

    def add_assets(self):
        self.assets_id += 1
        assets_folder = self.assets_folder + str(self.assets_id)
        assets_path = os.path.join(self.path, assets_folder)
        self.subwatcher = AssetsWatcher(assets_path, self.result_filename)
        self.data.setdefault("assets", []).append(assets_folder)
        save_json(self.result_path, self.data)


class AssetsWatcher(ResourceWatcher):
    def __init__(self, path: str, result_filename: str) -> None:
        path = create_folder(path)
        super().__init__(path)

        self.result_filename = os.path.join(path, result_filename)
        self.data = {}
        self.attack_id = 0
        self.current_attack = None

    def resolve_path(self, path: str) -> str:
        filename_ = filename(path)
        if self.current_attack:
            name, extension = os.path.splitext(filename_)
            filename_ = f"{name}_{self.current_attack}{self.attack_id}{extension}"
        return os.path.join(self.path, filename_)

    def add_attack(self, attack: str) -> None:
        self.attack_id = 0
        self.current_attack = attack

    def add_assets_statistics(
        self,
        video_path: str,
        watermark_path: str,
        embedding_statistics: EmbeddingStatistics,
        video_metrics: Optional[Iterable[MetricValue]],
        extracting_statistics: ExtractingStatistics,
        watermark_metrics: Optional[Iterable[MetricValue]],
    ) -> None:
        self.data["video"] = os.path.relpath(video_path, self.path)
        self.data["embedding"] = embedding_statistics.dictionary()
        self.data["watermark"] = os.path.relpath(watermark_path, self.path)
        self.data["extracting"] = extracting_statistics.dictionary()

        if video_metrics:
            video_metrics = list(map(dataclasses.asdict, video_metrics))
        if watermark_metrics:
            watermark_metrics = list(map(dataclasses.asdict, watermark_metrics))
        self.data["metrics"] = {
            "video": video_metrics,
            "watermark": watermark_metrics,
        }

        save_json(self.result_filename, self.data)

    def add_attack_statistics(
        self,
        watermark_path: str,
        extracting_statistics: ExtractingStatistics,
        watermark_metrics: Optional[Iterable[MetricValue]],
        params: Dict[str, Any],
    ) -> None:
        self.attack_id += 1
        attacks = self.data.setdefault("attacks", {})

        if watermark_metrics:
            watermark_metrics = list(map(dataclasses.asdict, watermark_metrics))

        attacks.setdefault(self.current_attack, []).append(
            {
                "watermark": os.path.relpath(watermark_path, self.path),
                "extracting": extracting_statistics.dictionary(),
                "metrics": watermark_metrics,
                "params": params,
            }
        )

        save_json(self.result_filename, self.data)


class HtmlReport(ResourceWatcher):
    def __init__(
        self,
        path: str,
        experiment_folder: str,
        assets_folder: str,
        result_filename: str,
    ) -> None:
        super().__init__(path)
        self.experiment_folder = experiment_folder
        self.assets_folder = assets_folder
        self.result_filename = result_filename
        self.result_path = os.path.join(path, result_filename)
        self.data = {}
        self.source_id = 0
        self.sources = {}
        create_folder(path)

    def resolve_path(self, source: str) -> str:
        return self.subwatcher.resolve_path(self.sources[source])

    def add_originals(
        self,
        video_paths: Iterable[str],
        watermark_holders: Iterable[WatermarkHolder],
    ) -> None:
        create_folder(self.path, self.assets_folder)
        self._save_originals(video_paths)
        self._save_originals(h.path for h in watermark_holders)

    def _save_originals(self, paths: Iterable[str]) -> None:
        for p in paths:
            self.source_id += 1
            name, extension = os.path.splitext(filename(p))
            new_filename = f"{name}_{self.source_id}{extension}"
            copied_path = os.path.join(
                self.path,
                self.assets_folder,
                new_filename,
            )
            shutil.copy2(p, copied_path)
            self.sources[p] = new_filename

    def add_algorithm(self, name: str) -> None:
        self.subwatcher = AlgorithmWatcher(
            os.path.join(self.path, name),
            self.experiment_folder,
            self.assets_folder,
            self.result_filename,
        )
        algorithms = self.data.setdefault("algorithms", [])
        algorithms.append(name)
        save_json(self.result_path, self.data)

    def add_experiment(self, params: Dict[str, Any]) -> None:
        experiment_path = self.subwatcher.add_experiment(params)
        algorithm = self.data["algorithms"][-1]

        experiments = self.data.setdefault("experiments", {})
        experiments.setdefault(algorithm, []).append(experiment_path)

        save_json(self.result_path, self.data)
