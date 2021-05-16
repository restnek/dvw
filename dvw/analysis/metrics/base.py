from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Union


class BaseMetric(Enum):
    def __new__(cls, value, full_name, calculate_fn, unit=None):
        obj = object().__new__(cls)
        obj._value_ = value
        obj.full_name = full_name
        obj.calculate = calculate_fn
        obj.unit = unit
        return obj


class Comparator(ABC):
    def __init__(self, precision):
        self.precision = precision

    @abstractmethod
    def compare(self, *args):
        pass


@dataclass
class MetricValue:
    metric: BaseMetric
    values: Union[List[Tuple[str, Union[float, int]]], float, int]
