from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Callable, Dict, Any

from dvw.util.base import PrettyDictionary


class BaseMetric(Enum):
    def __new__(
        cls,
        value: str,
        full_name: str,
        calculate_fn: Callable,
        unit: Optional[str] = None,
    ) -> "BaseMetric":
        obj = object().__new__(cls)
        obj._value_ = value
        obj.full_name = full_name
        obj.calculate = calculate_fn
        obj.unit = unit
        return obj


@dataclass
class MetricValue(PrettyDictionary):
    metric: BaseMetric
    value: float
    statistics: Optional[Dict[str, float]] = None

    def dictionary(self) -> Dict[str, Any]:
        data = {"Value": f"{self.value}{self.metric.unit or ''}"}
        if self.statistics:
            data.update(self.statistics)
        return data


class Comparator(ABC):
    def __init__(self, precision: int) -> None:
        self.precision = precision

    @abstractmethod
    def compare(self, *args) -> List[MetricValue]:
        pass
