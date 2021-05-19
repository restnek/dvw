import dataclasses
import json
import os.path
import shutil
from abc import ABC, abstractmethod
from typing import List, Iterable, Any, Dict, Optional

from dvw.core import ExtractingStatistics, EmbeddingStatistics
from dvw.metrics.base import MetricValue
from dvw.report.config import WatermarkHolder
from dvw.util import create_folder, filename


class Report(ABC):
    @abstractmethod
    def add_sources(
        self, video_path: List[str], watermark_holders: List[WatermarkHolder]
    ) -> None:
        pass

    @abstractmethod
    def new_algorithm(self, algorithm: str) -> None:
        pass

    @abstractmethod
    def new_experiment(self, params: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def new_assets(self) -> None:
        pass

    @abstractmethod
    def new_attack(self, attack: str) -> None:
        pass

    @abstractmethod
    def add_statistics(
        self,
        embedding_statistics: EmbeddingStatistics,
        embedding_metrics: Optional[List[MetricValue]],
        extracting_statistics: ExtractingStatistics,
        extracting_metrics: Optional[List[MetricValue]],
    ) -> None:
        pass

    @abstractmethod
    def add_attack_statistics(
        self,
        extracting_statistics: ExtractingStatistics,
        extracting_metrics: Optional[List[MetricValue]],
        params: Dict[str, Any],
    ) -> None:
        pass

    @abstractmethod
    def resolve_path(self, path: str) -> str:
        pass


class HtmlReport(Report):
    def __init__(
        self,
        report_path: str,
        experiment_folder: str = "exp",
        assets_folder: str = "assets",
        result_filename: str = "result.json",
    ) -> None:
        create_folder(report_path)
        self.report_path = report_path
        self.experiment_folder = experiment_folder
        self.assets_folder = assets_folder
        self.result_filename = result_filename

        self.sources = {}
        self.sources_id = 1
        self.current_algorithm = None
        self.current_experiment = 0
        self.current_experiment_data = {}
        self.current_assets = 0
        self.current_statistics = {}
        self.current_attack = ""
        self.current_attack_id = 0
        self.current_path = self.report_path

    def add_sources(
        self, video_paths: Iterable[str], watermark_holders: Iterable[WatermarkHolder]
    ) -> None:
        create_folder(self.report_path, self.assets_folder)
        self._add_source_path(video_paths)
        self._add_source_path(h.path for h in watermark_holders)

    def _add_source_path(self, paths: Iterable[str]) -> None:
        for p in paths:
            name, extension = os.path.splitext(filename(p))
            self.sources[p] = self.sources_id
            copied_path = os.path.join(
                self.report_path,
                self.assets_folder,
                f"{name}_{self.sources_id}{extension}",
            )
            shutil.copy2(p, copied_path)
            self.sources_id += 1

    def new_algorithm(self, algorithm: str) -> None:
        self.current_path = create_folder(self.report_path, algorithm)
        self.current_algorithm = algorithm
        self.current_experiment = 0
        self.current_experiment_data = {}
        self.current_assets = 0
        self.current_statistics = {}
        self.current_attack = ""
        self.current_attack_id = 0

    def new_experiment(self, params: Dict[str, Any]) -> None:
        self.current_experiment += 1
        self.current_assets = 0
        self.current_statistics = {}
        self.current_experiment_data = {"parameters": params}
        self.current_attack = ""
        self.current_attack_id = 0

        self.current_path = create_folder(
            self.report_path,
            self.current_algorithm,
            self.experiment_folder + str(self.current_experiment),
        )
        self._save_result(self.current_experiment_data)

    def new_assets(self) -> None:
        self.current_assets += 1
        self.current_statistics = {}
        self.current_attack = ""
        self.current_attack_id = 0
        self.current_experiment_data.setdefault("assets", []).append(
            self.assets_folder + str(self.current_assets)
        )

        self.current_path = create_folder(
            self.report_path,
            self.current_algorithm,
            self.experiment_folder + str(self.current_experiment),
            self.assets_folder + str(self.current_assets),
        )
        path = os.path.join(
            self.report_path,
            self.current_algorithm,
            self.experiment_folder + str(self.current_experiment),
        )
        self._save_result(self.current_experiment_data, path)

    def new_attack(self, attack: str) -> None:
        self.current_attack = attack
        self.current_attack_id = 0

    def add_statistics(
        self,
        embedding_statistics: EmbeddingStatistics,
        embedding_metrics: Optional[List[MetricValue]],
        extracting_statistics: ExtractingStatistics,
        extracting_metrics: Optional[List[MetricValue]],
    ) -> None:
        self.current_statistics["embedding"] = dataclasses.asdict(embedding_statistics)
        self.current_statistics["extracting"] = dataclasses.asdict(
            extracting_statistics
        )
        if embedding_metrics:
            embedding_metrics = list(map(dataclasses.asdict, embedding_metrics))
        if extracting_metrics:
            extracting_metrics = list(map(dataclasses.asdict, extracting_metrics))
        self.current_statistics["metrics"] = {
            "video": embedding_metrics,
            "watermark": extracting_metrics,
        }
        self._save_result(self.current_statistics)

    def add_attack_statistics(
        self,
        extracting_statistics: ExtractingStatistics,
        extracting_metrics: Optional[List[MetricValue]],
        params: Dict[str, Any],
    ) -> None:
        self.current_attack_id += 1

        if extracting_metrics:
            extracting_metrics = list(map(dataclasses.asdict, extracting_metrics))
        attacks = self.current_statistics.setdefault("attacks", [])
        attacks.append(
            {
                "extracting": dataclasses.asdict(extracting_statistics),
                "metrics": extracting_metrics,
                "params": params,
            }
        )
        self._save_result(self.current_statistics)

    def _save_result(self, value: Dict[str, Any], path: Optional[str] = None) -> None:
        path = path if path else self.current_path
        path = os.path.join(path, self.result_filename)
        with open(path, "w") as file:
            json.dump(value, file, default=str, indent=4)

    def resolve_path(self, source: str) -> str:
        source_id = self.sources[source]
        name, extension = os.path.splitext(filename(source))
        path = os.path.join(self.current_path, f"{name}_{source_id}")
        if self.current_attack:
            path += "_" + self.current_attack + str(self.current_attack_id)
        return path + extension
