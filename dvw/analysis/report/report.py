import os.path
from abc import ABC, abstractmethod
from typing import Optional, List

from dvw.analysis.metrics import MetricValue
from dvw.analysis.report.util import create_path
from dvw.core.core import EmbeddingStatistics, ExtractingStatistics
from dvw.core.util import isstr


class Report(ABC):
    @abstractmethod
    def resolve_path(
        self,
        path: str,
        algorithm_name: Optional[str] = None,
        attack_name: Optional[str] = None
    ) -> str:
        pass

    @abstractmethod
    def add_embedding_result(
        self,
        statistics: EmbeddingStatistics,
        metric_values: Optional[List[MetricValue]] = None
    ) -> None:
        pass

    @abstractmethod
    def add_extracting_result(
        self,
        statistics: ExtractingStatistics,
        metric_values: Optional[List[MetricValue]] = None
    ) -> None:
        pass

    @abstractmethod
    def add_attack_result(
        self,
        statistics: ExtractingStatistics,
        metric_values: Optional[List[MetricValue]] = None
    ) -> None:
        pass


class HtmlReport(Report):
    def __init__(self, report_path: str, experiment_folder: str = "exp") -> None:
        create_path(report_path)
        self.report_path = report_path
        self.experiment_folder = experiment_folder

        self.current_algorithm = None
        self.experiment_cnt = 0

    def resolve_path(
        self,
        path: str,
        algorithm_name: Optional[str] = None,
        attack_name: Optional[str] = None
    ) -> str:
        filename = os.path.split(path)[1]
        parts = (
            self.report_path,
            algorithm_name,
            self.experiment_folder + str(self.cnt),
            attack_name)

        path = os.path.join(*filter(isstr, parts))
        create_path(path)

        return os.path.join(path, filename)

    def new_algorithm(self, algorithm_name):
        self.current_algorithm = algorithm_name
        self._restore_state()

    def _restore_state(self):
        pass

    def new_experiment(self):
        pass  # self._init_experiment()

    def add_embedding_result(
        self,
        statistics: EmbeddingStatistics,
        metric_values: Optional[List[MetricValue]] = None
    ) -> None:
        pass
        # self.cnt += 1
        # self.experiment[]
        # print(statistics)
        # print(metric_values)

    def add_extracting_result(
        self,
        statistics: ExtractingStatistics,
        metric_values: Optional[List[MetricValue]] = None
    ) -> None:
        pass

    def add_attack_result(
        self,
        statistics: ExtractingStatistics,
        metric_values: Optional[List[MetricValue]] = None
    ) -> None:
        pass
